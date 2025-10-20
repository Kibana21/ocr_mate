"""Dual-extraction verification system (OCR + LLM counter-verification)"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

from .schema import ExtractionSchema, FieldDefinition, FieldType


class VerificationStatus(str, Enum):
    """Status of field verification"""
    MATCH = "match"  # OCR and LLM agree
    MISMATCH = "mismatch"  # OCR and LLM disagree
    OCR_ONLY = "ocr_only"  # Only OCR extracted this field
    LLM_ONLY = "llm_only"  # Only LLM extracted this field
    BOTH_MISSING = "both_missing"  # Neither extracted this field


class FieldVerification(BaseModel):
    """Verification result for a single field"""
    field_name: str
    ocr_value: Optional[Any] = None
    llm_value: Optional[Any] = None
    final_value: Optional[Any] = None
    status: VerificationStatus
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in final_value (0-1)"
    )
    ocr_confidence: Optional[float] = None
    llm_confidence: Optional[float] = None
    conflict_reason: Optional[str] = Field(
        default=None,
        description="Explanation if OCR and LLM disagree"
    )
    resolution_method: Optional[str] = Field(
        default=None,
        description="How conflict was resolved (if any)"
    )


class DocumentVerification(BaseModel):
    """Complete verification result for a document"""
    document_path: str
    schema_version: int
    field_verifications: List[FieldVerification]
    overall_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence across all fields"
    )
    match_rate: float = Field(
        ge=0.0, le=1.0,
        description="Percentage of fields where OCR and LLM agree"
    )
    needs_human_review: bool = Field(
        description="Whether human review is recommended"
    )

    def get_final_extraction(self) -> Dict[str, Any]:
        """Get final extraction result as dictionary"""
        return {
            fv.field_name: fv.final_value
            for fv in self.field_verifications
            if fv.final_value is not None
        }

    def get_conflicts(self) -> List[FieldVerification]:
        """Get fields with OCR/LLM conflicts"""
        return [
            fv for fv in self.field_verifications
            if fv.status == VerificationStatus.MISMATCH
        ]

    def get_high_confidence_fields(self, threshold: float = 0.8) -> List[str]:
        """Get field names with high confidence"""
        return [
            fv.field_name for fv in self.field_verifications
            if fv.confidence_score >= threshold
        ]

    def get_low_confidence_fields(self, threshold: float = 0.5) -> List[str]:
        """Get field names with low confidence (need review)"""
        return [
            fv.field_name for fv in self.field_verifications
            if fv.confidence_score < threshold
        ]


class ConflictResolutionStrategy(str, Enum):
    """Strategy for resolving OCR/LLM conflicts"""
    PREFER_LLM = "prefer_llm"  # Always prefer LLM value
    PREFER_OCR = "prefer_ocr"  # Always prefer OCR value
    HIGHER_CONFIDENCE = "higher_confidence"  # Choose value with higher confidence
    WEIGHTED_AVERAGE = "weighted_average"  # For numeric fields, compute weighted average
    HUMAN_REVIEW = "human_review"  # Flag for human review


class DualExtractionVerifier:
    """
    Verifies extractions by comparing OCR and LLM results

    This service runs both OCR extraction and LLM extraction, then compares
    the results to provide confidence scores and flag conflicts.

    Workflow:
        1. Run OCR extraction (fast, structured)
        2. Run LLM extraction (smart, context-aware)
        3. Compare results field-by-field
        4. Resolve conflicts using strategy
        5. Return verification result with confidence scores
    """

    def __init__(
        self,
        ocr_service,  # AzureDocumentIntelligenceService
        llm_extractor,  # Trained DSPy program from GEPA optimization
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.HIGHER_CONFIDENCE,
        human_review_threshold: float = 0.6
    ):
        """
        Initialize dual extraction verifier

        Args:
            ocr_service: Azure OCR service
            llm_extractor: Trained DSPy extraction program
            conflict_strategy: How to resolve OCR/LLM conflicts
            human_review_threshold: Confidence threshold below which human review is needed
        """
        self.ocr_service = ocr_service
        self.llm_extractor = llm_extractor
        self.conflict_strategy = conflict_strategy
        self.human_review_threshold = human_review_threshold

    def verify_extraction(
        self,
        document_path: str,
        schema: ExtractionSchema
    ) -> DocumentVerification:
        """
        Perform dual extraction and verification

        Args:
            document_path: Path to document
            schema: Extraction schema

        Returns:
            DocumentVerification with comparison results
        """
        # Step 1: Run OCR extraction
        ocr_result = self._extract_with_ocr(document_path, schema)

        # Step 2: Run LLM extraction
        llm_result = self._extract_with_llm(document_path, schema)

        # Step 3: Compare and verify each field
        field_verifications = []
        for field_def in schema.fields:
            field_verification = self._verify_field(
                field_def,
                ocr_result.get(field_def.name),
                llm_result.get(field_def.name)
            )
            field_verifications.append(field_verification)

        # Step 4: Calculate overall metrics
        match_count = sum(1 for fv in field_verifications if fv.status == VerificationStatus.MATCH)
        match_rate = match_count / len(schema.fields) if schema.fields else 0.0

        overall_confidence = sum(fv.confidence_score for fv in field_verifications) / len(field_verifications) if field_verifications else 0.0

        needs_review = overall_confidence < self.human_review_threshold or match_rate < 0.7

        return DocumentVerification(
            document_path=document_path,
            schema_version=schema.version,
            field_verifications=field_verifications,
            overall_confidence=overall_confidence,
            match_rate=match_rate,
            needs_human_review=needs_review
        )

    def _extract_with_ocr(
        self,
        document_path: str,
        schema: ExtractionSchema
    ) -> Dict[str, tuple]:
        """
        Extract using OCR + simple parsing

        Returns:
            Dict mapping field_name -> (value, confidence)
        """
        ocr_result = self.ocr_service.extract_text(document_path)

        # Simple keyword-based extraction
        import re
        field_values = {}
        text = ocr_result.full_text

        for field_def in schema.fields:
            # Build search patterns
            patterns = [
                field_def.name.replace("_", " "),
                field_def.display_name
            ]
            patterns.extend(field_def.extraction_hints)

            # Search for patterns
            for pattern in patterns:
                regex = rf"{re.escape(pattern)}\s*:?\s*([^\n]+)"
                match = re.search(regex, text, re.IGNORECASE)

                if match:
                    value = match.group(1).strip()
                    # Type conversion
                    typed_value = self._convert_value(value, field_def.data_type)
                    field_values[field_def.name] = (typed_value, 0.7)  # Medium confidence for OCR
                    break

        return field_values

    def _extract_with_llm(
        self,
        document_path: str,
        schema: ExtractionSchema
    ) -> Dict[str, tuple]:
        """
        Extract using trained LLM extractor

        Returns:
            Dict mapping field_name -> (value, confidence)
        """
        # Load image
        from ..gepa.image_processor import load_and_resize_image

        image = load_and_resize_image(document_path)

        # Run LLM extraction
        result = self.llm_extractor(document_image=image)

        # Extract values with confidence (default high for LLM)
        field_values = {}
        if hasattr(result, 'extracted_data'):
            extracted_data = result.extracted_data
            for field_def in schema.fields:
                if hasattr(extracted_data, field_def.name):
                    value = getattr(extracted_data, field_def.name)
                    if value is not None:
                        field_values[field_def.name] = (value, 0.85)  # High confidence for trained LLM

        return field_values

    def _verify_field(
        self,
        field_def: FieldDefinition,
        ocr_result: Optional[tuple],
        llm_result: Optional[tuple]
    ) -> FieldVerification:
        """
        Verify a single field by comparing OCR and LLM results

        Args:
            field_def: Field definition
            ocr_result: (value, confidence) from OCR or None
            llm_result: (value, confidence) from LLM or None

        Returns:
            FieldVerification with comparison result
        """
        ocr_value, ocr_conf = ocr_result if ocr_result else (None, None)
        llm_value, llm_conf = llm_result if llm_result else (None, None)

        # Determine status
        if ocr_value is None and llm_value is None:
            status = VerificationStatus.BOTH_MISSING
            final_value = None
            confidence = 0.0
            reason = "Neither OCR nor LLM extracted this field"
            method = None

        elif ocr_value is None:
            status = VerificationStatus.LLM_ONLY
            final_value = llm_value
            confidence = llm_conf * 0.8  # Slightly lower confidence when only one source
            reason = "Only LLM extracted this field"
            method = "llm_only"

        elif llm_value is None:
            status = VerificationStatus.OCR_ONLY
            final_value = ocr_value
            confidence = ocr_conf * 0.8
            reason = "Only OCR extracted this field"
            method = "ocr_only"

        else:
            # Both extracted - compare
            values_match = self._values_match(ocr_value, llm_value, field_def.data_type)

            if values_match:
                status = VerificationStatus.MATCH
                final_value = llm_value  # Prefer LLM when they match
                confidence = min(ocr_conf, llm_conf) + 0.15  # Boost confidence when both agree
                confidence = min(confidence, 1.0)
                reason = None
                method = "both_agree"

            else:
                status = VerificationStatus.MISMATCH
                reason = f"OCR extracted '{ocr_value}', LLM extracted '{llm_value}'"

                # Resolve conflict using strategy
                if self.conflict_strategy == ConflictResolutionStrategy.PREFER_LLM:
                    final_value = llm_value
                    confidence = llm_conf
                    method = "prefer_llm"

                elif self.conflict_strategy == ConflictResolutionStrategy.PREFER_OCR:
                    final_value = ocr_value
                    confidence = ocr_conf
                    method = "prefer_ocr"

                elif self.conflict_strategy == ConflictResolutionStrategy.HIGHER_CONFIDENCE:
                    if llm_conf >= ocr_conf:
                        final_value = llm_value
                        confidence = llm_conf
                        method = "higher_confidence_llm"
                    else:
                        final_value = ocr_value
                        confidence = ocr_conf
                        method = "higher_confidence_ocr"

                elif self.conflict_strategy == ConflictResolutionStrategy.WEIGHTED_AVERAGE:
                    if field_def.data_type in [FieldType.NUMBER, FieldType.CURRENCY]:
                        try:
                            ocr_num = float(str(ocr_value).replace('$', '').replace(',', ''))
                            llm_num = float(str(llm_value).replace('$', '').replace(',', ''))
                            final_value = (ocr_num * ocr_conf + llm_num * llm_conf) / (ocr_conf + llm_conf)
                            confidence = (ocr_conf + llm_conf) / 2
                            method = "weighted_average"
                        except:
                            # Fall back to higher confidence
                            final_value = llm_value if llm_conf >= ocr_conf else ocr_value
                            confidence = max(ocr_conf, llm_conf)
                            method = "fallback_higher_confidence"
                    else:
                        final_value = llm_value if llm_conf >= ocr_conf else ocr_value
                        confidence = max(ocr_conf, llm_conf)
                        method = "higher_confidence"

                else:  # HUMAN_REVIEW
                    final_value = None
                    confidence = 0.0
                    method = "needs_human_review"

        return FieldVerification(
            field_name=field_def.name,
            ocr_value=ocr_value,
            llm_value=llm_value,
            final_value=final_value,
            status=status,
            confidence_score=confidence,
            ocr_confidence=ocr_conf,
            llm_confidence=llm_conf,
            conflict_reason=reason,
            resolution_method=method
        )

    def _values_match(self, value1: Any, value2: Any, field_type: FieldType) -> bool:
        """Check if two values match (with type-specific tolerance)"""
        if value1 == value2:
            return True

        # Normalize for comparison
        str1 = str(value1).strip().lower()
        str2 = str(value2).strip().lower()

        if str1 == str2:
            return True

        # Type-specific matching
        if field_type in [FieldType.NUMBER, FieldType.CURRENCY]:
            try:
                # Remove currency symbols and commas
                num1 = float(str1.replace('$', '').replace(',', '').replace('€', '').replace('£', ''))
                num2 = float(str2.replace('$', '').replace(',', '').replace('€', '').replace('£', ''))
                # Allow 1% tolerance for numeric fields
                return abs(num1 - num2) / max(abs(num1), abs(num2), 1) < 0.01
            except:
                return False

        elif field_type == FieldType.DATE:
            # TODO: Normalize date formats and compare
            return str1 == str2

        return False

    def _convert_value(self, value: str, field_type: FieldType) -> Any:
        """Convert string value to appropriate type"""
        if field_type == FieldType.NUMBER:
            try:
                return float(value.replace(',', ''))
            except:
                return value

        elif field_type == FieldType.CURRENCY:
            try:
                return float(value.replace('$', '').replace(',', '').replace('€', '').replace('£', ''))
            except:
                return value

        elif field_type == FieldType.BOOLEAN:
            value_lower = value.lower()
            if value_lower in ['yes', 'true', '1', 'y']:
                return True
            elif value_lower in ['no', 'false', '0', 'n']:
                return False
            return value

        return value
