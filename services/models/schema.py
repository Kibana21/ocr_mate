"""
Schema Data Models for OCR Mate

Represents the extraction schema that users define for each document type.
These models will be used to dynamically create DSPy signatures.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class FieldType(str, Enum):
    """Supported field data types"""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    BOOLEAN = "boolean"


class FieldValidation(BaseModel):
    """Validation rules for a field"""
    pattern: Optional[str] = None  # Regex pattern
    min_value: Optional[float] = None  # For numbers/currency
    max_value: Optional[float] = None
    min_length: Optional[int] = None  # For text
    max_length: Optional[int] = None
    example: Optional[str] = None  # Example value


class FieldDefinition(BaseModel):
    """Definition of a single extraction field"""
    name: str = Field(..., description="Field name (snake_case)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this field represents")
    data_type: FieldType = Field(..., description="Data type")
    required: bool = Field(default=True, description="Is this field required?")
    validation: Optional[FieldValidation] = None
    extraction_hints: List[str] = Field(
        default_factory=list,
        description="Tips for extraction (e.g., 'Usually in top-right corner')"
    )


class ExtractionSchema(BaseModel):
    """Complete extraction schema for a document type"""
    version: int = Field(default=1, description="Schema version")
    fields: List[FieldDefinition] = Field(..., description="List of fields to extract")

    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get field definition by name"""
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def to_prompt_description(self) -> str:
        """Generate human-readable description for LLM prompt"""
        lines = ["Extract the following fields from the document:"]
        for field in self.fields:
            required_str = "(required)" if field.required else "(optional)"
            lines.append(f"- {field.display_name} ({field.data_type.value}) {required_str}: {field.description}")

            if field.extraction_hints:
                for hint in field.extraction_hints:
                    lines.append(f"  • {hint}")

        return "\n".join(lines)


class GroundTruthExample(BaseModel):
    """A single ground truth example for training"""
    document_path: str = Field(..., description="Path to document image")
    labeled_values: Dict[str, Any] = Field(..., description="field_name -> value")

    def get_value(self, field_name: str) -> Any:
        """Get labeled value for a field"""
        return self.labeled_values.get(field_name)


# Example usage:
if __name__ == "__main__":
    # Example: Receipt schema (from your gepa_receipt_optimization.py)
    receipt_schema = ExtractionSchema(
        version=1,
        fields=[
            FieldDefinition(
                name="before_tax_total",
                display_name="Before-Tax Total",
                description="Subtotal before taxes are applied",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=[
                    "Look for 'Subtotal' label",
                    "Usually appears before tax line"
                ]
            ),
            FieldDefinition(
                name="after_tax_total",
                display_name="After-Tax Total",
                description="Final total including all taxes",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=[
                    "Look for 'Total', 'Amount', or 'Balance' label",
                    "Usually at the bottom of receipt"
                ]
            )
        ]
    )

    print(receipt_schema.to_prompt_description())
