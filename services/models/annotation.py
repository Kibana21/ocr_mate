"""Models for OCR-assisted ground truth annotation"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .schema import ExtractionSchema, FieldDefinition


class AnnotationSource(str, Enum):
    """Source of annotation value"""
    OCR_AUTO = "ocr_auto"  # Automatically extracted by OCR
    USER_EDITED = "user_edited"  # User manually corrected OCR value
    USER_MANUAL = "user_manual"  # User manually entered (OCR failed)


class FieldAnnotation(BaseModel):
    """Single field annotation with source tracking"""
    field_name: str
    value: Any
    source: AnnotationSource
    ocr_confidence: Optional[float] = Field(
        default=None,
        description="OCR confidence if value came from OCR"
    )
    user_verified: bool = Field(
        default=False,
        description="Whether user has reviewed and verified this value"
    )


class DocumentAnnotation(BaseModel):
    """
    Complete annotation for a document (ground truth example)

    This represents a user's ground truth annotation, which may be:
    - Auto-filled by OCR (needs user verification)
    - Manually corrected by user
    - Manually entered by user
    """
    document_path: str
    schema_version: int
    annotations: List[FieldAnnotation]
    ocr_full_text: Optional[str] = Field(
        default=None,
        description="Full OCR text for reference"
    )
    is_complete: bool = Field(
        default=False,
        description="Whether all required fields are annotated and verified"
    )

    def get_field_value(self, field_name: str) -> Optional[Any]:
        """Get value for specific field"""
        for annotation in self.annotations:
            if annotation.field_name == field_name:
                return annotation.value
        return None

    def set_field_value(
        self,
        field_name: str,
        value: Any,
        source: AnnotationSource,
        ocr_confidence: Optional[float] = None
    ):
        """Set or update field value"""
        # Remove existing annotation for this field
        self.annotations = [a for a in self.annotations if a.field_name != field_name]

        # Add new annotation
        self.annotations.append(FieldAnnotation(
            field_name=field_name,
            value=value,
            source=source,
            ocr_confidence=ocr_confidence,
            user_verified=(source == AnnotationSource.USER_EDITED or source == AnnotationSource.USER_MANUAL)
        ))

    def mark_field_verified(self, field_name: str):
        """Mark field as user-verified (user confirms OCR value is correct)"""
        for annotation in self.annotations:
            if annotation.field_name == field_name:
                annotation.user_verified = True
                break

    def to_ground_truth(self) -> Dict[str, Any]:
        """Convert to ground truth format for GEPA training"""
        return {
            annotation.field_name: annotation.value
            for annotation in self.annotations
        }

    def get_completion_status(self, schema: ExtractionSchema) -> Dict[str, Any]:
        """Get annotation completion status"""
        required_fields = [f.name for f in schema.fields if f.required]
        annotated_fields = [a.field_name for a in self.annotations]
        verified_fields = [a.field_name for a in self.annotations if a.user_verified]

        missing_required = [f for f in required_fields if f not in annotated_fields]
        unverified_required = [f for f in required_fields if f in annotated_fields and f not in verified_fields]

        return {
            'total_fields': len(schema.fields),
            'annotated_fields': len(annotated_fields),
            'verified_fields': len(verified_fields),
            'missing_required': missing_required,
            'unverified_required': unverified_required,
            'is_complete': len(missing_required) == 0 and len(unverified_required) == 0
        }


class OCRAssistedAnnotationService:
    """
    Service for creating OCR-assisted annotations

    This service uses OCR to pre-fill annotation values, which users can then
    verify or correct in the UI.

    Workflow:
        1. User uploads document
        2. Service runs OCR extraction
        3. Service attempts to match OCR text to schema fields using LLM
        4. Service returns DocumentAnnotation with pre-filled values
        5. User reviews/corrects in UI
        6. User marks annotation as complete
    """

    def __init__(
        self,
        ocr_service,  # AzureDocumentIntelligenceService
        extraction_llm=None  # Optional: DSPy LLM for smart field matching
    ):
        """
        Initialize annotation service

        Args:
            ocr_service: AzureDocumentIntelligenceService instance
            extraction_llm: Optional DSPy LLM for intelligent field extraction
        """
        self.ocr_service = ocr_service
        self.extraction_llm = extraction_llm

    def create_annotation(
        self,
        document_path: str,
        schema: ExtractionSchema
    ) -> DocumentAnnotation:
        """
        Create OCR-assisted annotation for a document

        Args:
            document_path: Path to document file
            schema: Extraction schema defining fields to extract

        Returns:
            DocumentAnnotation with OCR-extracted values (needs user verification)
        """
        # Step 1: Run OCR
        ocr_result = self.ocr_service.extract_text(document_path)

        # Step 2: Extract field values from OCR text
        if self.extraction_llm:
            # Use LLM for intelligent extraction
            field_values = self._extract_with_llm(ocr_result, schema)
        else:
            # Use simple keyword matching
            field_values = self._extract_with_keywords(ocr_result, schema)

        # Step 3: Create annotations
        annotations = []
        for field_def in schema.fields:
            if field_def.name in field_values:
                value, confidence = field_values[field_def.name]
                annotations.append(FieldAnnotation(
                    field_name=field_def.name,
                    value=value,
                    source=AnnotationSource.OCR_AUTO,
                    ocr_confidence=confidence,
                    user_verified=False
                ))

        return DocumentAnnotation(
            document_path=document_path,
            schema_version=schema.version,
            annotations=annotations,
            ocr_full_text=ocr_result.full_text,
            is_complete=False
        )

    def _extract_with_keywords(
        self,
        ocr_result,
        schema: ExtractionSchema
    ) -> Dict[str, tuple]:
        """
        Simple keyword-based extraction from OCR text

        Returns:
            Dict mapping field_name -> (value, confidence)
        """
        import re

        field_values = {}
        text = ocr_result.full_text.lower()

        for field_def in schema.fields:
            # Build search patterns from field name and hints
            patterns = [
                field_def.name.replace("_", " "),
                field_def.display_name.lower()
            ]
            patterns.extend([hint.lower() for hint in field_def.extraction_hints])

            # Search for patterns
            for pattern in patterns:
                # Look for "pattern: value" or "pattern value"
                regex = rf"{re.escape(pattern)}\s*:?\s*([^\n]+)"
                match = re.search(regex, text, re.IGNORECASE)

                if match:
                    value = match.group(1).strip()
                    field_values[field_def.name] = (value, 0.5)  # Low confidence for keyword matching
                    break

        return field_values

    def _extract_with_llm(
        self,
        ocr_result,
        schema: ExtractionSchema
    ) -> Dict[str, tuple]:
        """
        Intelligent LLM-based extraction from OCR text

        Returns:
            Dict mapping field_name -> (value, confidence)
        """
        # TODO: Implement LLM-based extraction
        # This would use DSPy to extract fields more intelligently
        # For now, fall back to keyword matching
        return self._extract_with_keywords(ocr_result, schema)
