"""Azure Document Intelligence OCR Service"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field

try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class OCRWord(BaseModel):
    """Single word from OCR with position"""
    text: str
    confidence: float
    bounding_box: List[float] = Field(description="[x1, y1, x2, y2, x3, y3, x4, y4]")


class OCRLine(BaseModel):
    """Line of text from OCR"""
    text: str
    words: List[OCRWord]
    bounding_box: List[float]
    confidence: float = Field(default=1.0)


class OCRPage(BaseModel):
    """Single page OCR result"""
    page_number: int
    text: str = Field(description="All text on this page")
    lines: List[OCRLine]
    width: float = Field(description="Page width in pixels")
    height: float = Field(description="Page height in pixels")

    def get_text_in_region(self, x: float, y: float, width: float, height: float) -> str:
        """Get text within a specific region of the page"""
        region_text = []
        for line in self.lines:
            # Simple bounding box intersection check
            if self._box_intersects_region(line.bounding_box, x, y, width, height):
                region_text.append(line.text)
        return "\n".join(region_text)

    def _box_intersects_region(self, box: List[float], x: float, y: float, w: float, h: float) -> bool:
        """Check if bounding box intersects with region"""
        # box is [x1, y1, x2, y2, x3, y3, x4, y4]
        box_x_min = min(box[0], box[2], box[4], box[6])
        box_x_max = max(box[0], box[2], box[4], box[6])
        box_y_min = min(box[1], box[3], box[5], box[7])
        box_y_max = max(box[1], box[3], box[5], box[7])

        region_x_max = x + w
        region_y_max = y + h

        # Check for intersection
        return not (box_x_max < x or box_x_min > region_x_max or
                    box_y_max < y or box_y_min > region_y_max)


class OCRResult(BaseModel):
    """Complete OCR result for a document"""
    pages: List[OCRPage]
    full_text: str = Field(description="All text from all pages")
    model_id: str = Field(default="prebuilt-layout")

    def get_page(self, page_number: int) -> Optional[OCRPage]:
        """Get specific page by number"""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None

    def search_text(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text across all pages"""
        results = []
        search_query = query if case_sensitive else query.lower()

        for page in self.pages:
            page_text = page.text if case_sensitive else page.text.lower()
            if search_query in page_text:
                results.append({
                    'page_number': page.page_number,
                    'text': page.text,
                    'query': query
                })
        return results


class AzureDocumentIntelligenceService:
    """
    OCR service using Azure Document Intelligence (formerly Form Recognizer)

    This service extracts text and layout information from documents.

    Usage:
        service = AzureDocumentIntelligenceService(
            endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
            api_key=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        )

        result = service.extract_text("path/to/document.pdf")
        print(result.full_text)

        # Get specific page
        page1 = result.get_page(1)
        print(page1.text)
    """

    def __init__(self, endpoint: str, api_key: str):
        """
        Initialize Azure Document Intelligence client

        Args:
            endpoint: Azure endpoint URL (e.g., https://xxx.cognitiveservices.azure.com)
            api_key: Azure API key
        """
        if not AZURE_AVAILABLE:
            raise ImportError(
                "Azure Document Intelligence SDK not installed. "
                "Install with: pip install azure-ai-documentintelligence"
            )

        self.endpoint = endpoint
        self.api_key = api_key
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )

    def extract_text(
        self,
        document_path: str,
        model_id: str = "prebuilt-layout"
    ) -> OCRResult:
        """
        Extract text and layout from document

        Args:
            document_path: Path to document file (PDF, JPG, PNG, etc.)
            model_id: Azure model to use:
                - "prebuilt-read": Fast text extraction only
                - "prebuilt-layout": Text + layout (tables, structure)
                - "prebuilt-document": Text + key-value pairs

        Returns:
            OCRResult with pages, lines, words, and bounding boxes
        """
        document_path = Path(document_path)

        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")

        # Read document
        with open(document_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                analyze_request=f,
                content_type="application/octet-stream"
            )

        # Wait for result
        result = poller.result()

        # Convert to our format
        pages = []
        for page in result.pages:
            ocr_lines = []

            # Process lines
            if hasattr(page, 'lines') and page.lines:
                for line in page.lines:
                    # Get words for this line
                    words = []
                    if hasattr(line, 'spans') and line.spans:
                        # Extract words from line
                        for word in page.words:
                            # Check if word is in this line's span
                            word_in_line = any(
                                span.offset <= word.span.offset < span.offset + span.length
                                for span in line.spans
                            )
                            if word_in_line:
                                words.append(OCRWord(
                                    text=word.content,
                                    confidence=word.confidence if hasattr(word, 'confidence') else 1.0,
                                    bounding_box=word.polygon if hasattr(word, 'polygon') else []
                                ))

                    ocr_lines.append(OCRLine(
                        text=line.content,
                        words=words,
                        bounding_box=line.polygon if hasattr(line, 'polygon') else [],
                        confidence=1.0  # Line-level confidence not provided by Azure
                    ))

            # Fallback: if no lines, use words directly
            elif hasattr(page, 'words') and page.words:
                # Group words into lines (simple approach: same Y coordinate)
                from collections import defaultdict
                y_groups = defaultdict(list)

                for word in page.words:
                    if hasattr(word, 'polygon') and len(word.polygon) >= 2:
                        y_coord = round(word.polygon[1])  # Use top Y coordinate
                        y_groups[y_coord].append(word)

                # Convert groups to lines
                for y_coord in sorted(y_groups.keys()):
                    word_group = sorted(y_groups[y_coord], key=lambda w: w.polygon[0])
                    line_text = " ".join(w.content for w in word_group)
                    words = [
                        OCRWord(
                            text=w.content,
                            confidence=w.confidence if hasattr(w, 'confidence') else 1.0,
                            bounding_box=w.polygon if hasattr(w, 'polygon') else []
                        )
                        for w in word_group
                    ]

                    # Calculate line bounding box from words
                    if words and words[0].bounding_box:
                        x_coords = [coord for word in words for coord in word.bounding_box[::2]]
                        y_coords = [coord for word in words for coord in word.bounding_box[1::2]]
                        line_bbox = [
                            min(x_coords), min(y_coords),
                            max(x_coords), min(y_coords),
                            max(x_coords), max(y_coords),
                            min(x_coords), max(y_coords)
                        ]
                    else:
                        line_bbox = []

                    ocr_lines.append(OCRLine(
                        text=line_text,
                        words=words,
                        bounding_box=line_bbox,
                        confidence=1.0
                    ))

            pages.append(OCRPage(
                page_number=page.page_number,
                text="\n".join(line.text for line in ocr_lines),
                lines=ocr_lines,
                width=page.width if hasattr(page, 'width') else 0,
                height=page.height if hasattr(page, 'height') else 0
            ))

        full_text = "\n\n".join(f"--- Page {page.page_number} ---\n{page.text}" for page in pages)

        return OCRResult(
            pages=pages,
            full_text=full_text,
            model_id=model_id
        )

    def extract_key_value_pairs(self, document_path: str) -> Dict[str, Any]:
        """
        Extract key-value pairs from document (e.g., form fields)

        Args:
            document_path: Path to document

        Returns:
            Dictionary of extracted key-value pairs
        """
        document_path = Path(document_path)

        with open(document_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-document",
                analyze_request=f,
                content_type="application/octet-stream"
            )

        result = poller.result()

        # Extract key-value pairs
        key_value_pairs = {}
        if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
            for kv in result.key_value_pairs:
                if kv.key and kv.value:
                    key_text = kv.key.content if hasattr(kv.key, 'content') else str(kv.key)
                    value_text = kv.value.content if hasattr(kv.value, 'content') else str(kv.value)
                    key_value_pairs[key_text] = value_text

        return key_value_pairs

    @classmethod
    def from_env(cls) -> "AzureDocumentIntelligenceService":
        """
        Create service from environment variables

        Requires:
            AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
            AZURE_DOCUMENT_INTELLIGENCE_KEY
        """
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if not endpoint or not api_key:
            raise ValueError(
                "Missing Azure credentials. Set environment variables:\n"
                "  AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT\n"
                "  AZURE_DOCUMENT_INTELLIGENCE_KEY"
            )

        return cls(endpoint=endpoint, api_key=api_key)
