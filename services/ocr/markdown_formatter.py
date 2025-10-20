"""Format OCR results as structured markdown for LLM grounding"""

from typing import List, Optional
from .azure_service import OCRResult, OCRPage, OCRLine


class OCRMarkdownFormatter:
    """
    Formats OCR results as structured markdown for LLM consumption

    This provides structured text grounding that helps LLMs:
    - Understand document layout
    - Reference specific sections
    - Extract fields more accurately
    - Handle tables and lists
    """

    def __init__(
        self,
        include_confidence: bool = False,
        include_bounding_boxes: bool = False,
        preserve_layout: bool = True
    ):
        """
        Initialize markdown formatter

        Args:
            include_confidence: Add confidence scores to output
            include_bounding_boxes: Add bounding box coordinates
            preserve_layout: Try to preserve visual layout with spacing
        """
        self.include_confidence = include_confidence
        self.include_bounding_boxes = include_bounding_boxes
        self.preserve_layout = preserve_layout

    def format(self, ocr_result: OCRResult) -> str:
        """
        Format complete OCR result as markdown

        Args:
            ocr_result: OCR result from Azure Document Intelligence

        Returns:
            Formatted markdown string
        """
        markdown_parts = []

        # Header
        markdown_parts.append("# Document OCR Text\n")
        markdown_parts.append(f"*Extracted using {ocr_result.model_id}*\n")

        # Process each page
        for page in ocr_result.pages:
            page_md = self._format_page(page)
            markdown_parts.append(page_md)

        return "\n".join(markdown_parts)

    def format_compact(self, ocr_result: OCRResult) -> str:
        """
        Format OCR result in compact form (just text, no metadata)

        This is best for LLM input to minimize token usage.

        Args:
            ocr_result: OCR result

        Returns:
            Compact markdown string
        """
        parts = []

        for page in ocr_result.pages:
            if len(ocr_result.pages) > 1:
                parts.append(f"## Page {page.page_number}\n")
            parts.append(page.text)

        return "\n\n".join(parts)

    def format_with_layout(self, ocr_result: OCRResult) -> str:
        """
        Format OCR with layout hints for better structure preservation

        This includes:
        - Section headers (larger text)
        - Tables (detected by alignment)
        - Lists (detected by bullets)
        - Key-value pairs (detected by colons)

        Args:
            ocr_result: OCR result

        Returns:
            Layout-aware markdown
        """
        parts = []

        for page in ocr_result.pages:
            if len(ocr_result.pages) > 1:
                parts.append(f"## Page {page.page_number}\n")

            # Detect structure
            structured_text = self._detect_structure(page)
            parts.append(structured_text)

        return "\n\n".join(parts)

    def _format_page(self, page: OCRPage) -> str:
        """Format single page as markdown"""
        parts = []

        # Page header
        parts.append(f"\n## Page {page.page_number}")

        if self.include_bounding_boxes:
            parts.append(f"*Dimensions: {page.width}x{page.height}*\n")

        # Page content
        if self.preserve_layout:
            content = self._format_with_spacing(page)
        else:
            content = page.text

        parts.append(content)

        return "\n".join(parts)

    def _format_with_spacing(self, page: OCRPage) -> str:
        """Format page preserving vertical spacing"""
        lines = []

        prev_y = 0
        for line in page.lines:
            # Get Y coordinate (top of bounding box)
            if line.bounding_box and len(line.bounding_box) >= 2:
                y = line.bounding_box[1]

                # Add blank line if large vertical gap
                if prev_y > 0 and y - prev_y > 50:  # 50px gap threshold
                    lines.append("")

                prev_y = y

            # Add line text
            line_text = line.text

            if self.include_confidence and hasattr(line, 'confidence'):
                line_text += f" `[conf: {line.confidence:.2f}]`"

            lines.append(line_text)

        return "\n".join(lines)

    def _detect_structure(self, page: OCRPage) -> str:
        """Detect and format document structure"""
        lines = []

        for i, line in enumerate(page.lines):
            text = line.text.strip()

            # Skip empty lines
            if not text:
                continue

            # Detect headers (all caps, short lines)
            if self._is_header(text, line):
                lines.append(f"### {text}\n")

            # Detect key-value pairs
            elif ':' in text and not text.endswith(':'):
                key, value = text.split(':', 1)
                lines.append(f"**{key.strip()}**: {value.strip()}")

            # Detect list items
            elif self._is_list_item(text):
                lines.append(f"- {text.lstrip('•-*').strip()}")

            # Regular text
            else:
                lines.append(text)

        return "\n".join(lines)

    def _is_header(self, text: str, line: OCRLine) -> bool:
        """Detect if line is likely a header"""
        # Short, all caps or title case
        if len(text) < 50 and (text.isupper() or text.istitle()):
            return True

        # Could also check font size from bounding box height
        # (larger bounding box height = larger font = likely header)

        return False

    def _is_list_item(self, text: str) -> bool:
        """Detect if line is a list item"""
        return text.startswith(('•', '-', '*', '·')) or \
               (len(text) > 2 and text[0].isdigit() and text[1] in '.)')


def create_llm_grounding_prompt(
    ocr_result: OCRResult,
    schema_description: str,
    compact: bool = True
) -> str:
    """
    Create LLM prompt with OCR text as grounding

    This is the optimal format for LLM extraction with OCR grounding.

    Args:
        ocr_result: OCR result from document
        schema_description: Description of fields to extract
        compact: Use compact format (recommended for token efficiency)

    Returns:
        Formatted prompt string
    """
    formatter = OCRMarkdownFormatter()

    if compact:
        ocr_text = formatter.format_compact(ocr_result)
    else:
        ocr_text = formatter.format_with_layout(ocr_result)

    prompt = f"""The document has been OCR-processed. Below is the extracted text:

---
{ocr_text}
---

Extract the following fields from the document:

{schema_description}

Use the OCR text above as your primary reference. The document image is also provided for visual context.
"""

    return prompt


def format_for_dual_input(ocr_result: OCRResult) -> dict:
    """
    Format OCR for dual input (image + OCR text)

    Returns dictionary with both compact and detailed formats.

    Args:
        ocr_result: OCR result

    Returns:
        {
            'compact_text': str,  # For LLM input (minimal tokens)
            'structured_text': str,  # With layout hints
            'full_markdown': str,  # Complete with metadata
            'raw_text': str  # Just the text, no formatting
        }
    """
    formatter = OCRMarkdownFormatter()

    return {
        'compact_text': formatter.format_compact(ocr_result),
        'structured_text': formatter.format_with_layout(ocr_result),
        'full_markdown': formatter.format(ocr_result),
        'raw_text': ocr_result.full_text
    }


def create_table_from_ocr(page: OCRPage, region: tuple = None) -> str:
    """
    Detect and format tables from OCR data

    Args:
        page: OCR page
        region: Optional (x, y, width, height) to extract table from specific region

    Returns:
        Markdown table string
    """
    # This is a simplified implementation
    # Azure Document Intelligence has better table detection via prebuilt-layout model

    # TODO: Implement table detection using bounding box alignment
    # For now, return simple formatted text

    if region:
        # Extract text from region
        x, y, w, h = region
        text = page.get_text_in_region(x, y, w, h)
        return text

    return page.text
