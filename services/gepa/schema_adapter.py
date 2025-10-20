"""
Schema Adapter - Convert JSON schemas to DSPy signatures

Dynamically creates DSPy signatures and Pydantic models from
user-defined extraction schemas.
"""

import dspy
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, create_model
from services.models.schema import ExtractionSchema, FieldDefinition, FieldType
import re


def field_type_to_python_type(field_type: FieldType) -> Type:
    """Map FieldType to Python type"""
    type_mapping = {
        FieldType.TEXT: str,
        FieldType.NUMBER: float,
        FieldType.CURRENCY: float,
        FieldType.DATE: str,  # ISO format string
        FieldType.EMAIL: str,
        FieldType.PHONE: str,
        FieldType.ADDRESS: str,
        FieldType.BOOLEAN: bool,
    }
    return type_mapping.get(field_type, str)


def create_pydantic_model_from_schema(schema: ExtractionSchema) -> Type[BaseModel]:
    """
    Dynamically create a Pydantic model from an ExtractionSchema.

    This model will be used as the OutputField in the DSPy signature.

    Args:
        schema: ExtractionSchema defining fields to extract

    Returns:
        Dynamically created Pydantic BaseModel class
    """
    # Build field definitions for Pydantic
    field_definitions = {}

    for field_def in schema.fields:
        # Get Python type
        python_type = field_type_to_python_type(field_def.data_type)

        # Make optional if not required
        if not field_def.required:
            python_type = Optional[python_type]

        # Create Field with metadata
        pydantic_field = Field(
            default=None if not field_def.required else ...,
            description=field_def.description
        )

        field_definitions[field_def.name] = (python_type, pydantic_field)

    # Create dynamic model
    DynamicExtractionModel = create_model(
        'DynamicExtractionModel',
        **field_definitions,
        __base__=BaseModel
    )

    # Add field validator for XML parsing (like your ReceiptTotals)
    # This handles LLM responses that wrap values in XML tags
    @field_validator('*', mode='before')
    @classmethod
    def extract_from_xml(cls, v):
        """Extract value from XML tags if present"""
        if isinstance(v, str):
            # Try to extract from XML tags: <field_name>value</field_name>
            match = re.search(r'<[^>]+>([^<]+)</[^>]+>', v)
            if match:
                v = match.group(1).strip()

            # Try to parse as number/currency
            if v:
                # Remove currency symbols
                v_clean = v.replace('$', '').replace(',', '').strip()
                try:
                    return float(v_clean)
                except ValueError:
                    return v
        return v

    # Attach validator to model
    for field_name in field_definitions.keys():
        setattr(DynamicExtractionModel, f'validate_{field_name}', extract_from_xml)

    return DynamicExtractionModel


def create_dspy_signature_from_schema(
    schema: ExtractionSchema,
    extraction_model: Type[BaseModel],
    use_ocr_grounding: bool = False
) -> Type[dspy.Signature]:
    """
    Create a DSPy Signature from an ExtractionSchema.

    Args:
        schema: ExtractionSchema defining fields
        extraction_model: Pydantic model for output structure
        use_ocr_grounding: If True, include OCR text input field for grounding

    Returns:
        DSPy Signature class
    """
    if use_ocr_grounding:
        # Dual input mode: Image + OCR text
        instruction = f"""Extract structured data from the document using BOTH the image and OCR text.

The OCR text provides the textual content for reference. Use the image for visual context and verification.

{schema.to_prompt_description()}

Return values in a structured format. Cross-reference between OCR text and image for accuracy."""

        class DynamicExtractionWithOCR(dspy.Signature):
            __doc__ = instruction

            document_image: dspy.Image = dspy.InputField(
                desc="Document image for visual context"
            )
            ocr_text: str = dspy.InputField(
                desc="OCR-extracted text from the document for textual reference"
            )
            extracted_data: extraction_model = dspy.OutputField(
                desc="Extracted structured data"
            )

        return DynamicExtractionWithOCR

    else:
        # Vision-only mode (original)
        instruction = f"""Extract structured data from the document image.

{schema.to_prompt_description()}

Return values in a structured format. Be precise and extract exact values from the document."""

        class DynamicExtraction(dspy.Signature):
            __doc__ = instruction

            document_image: dspy.Image = dspy.InputField(
                desc="Document image to extract data from"
            )
            extracted_data: extraction_model = dspy.OutputField(
                desc="Extracted structured data"
            )

        return DynamicExtraction


class SchemaAdapter:
    """
    Adapter that converts ExtractionSchema to DSPy components.

    Usage:
        # Vision-only mode (original)
        adapter = SchemaAdapter(schema)
        signature = adapter.get_dspy_signature()
        program = dspy.Predict(signature)

        # OCR-grounded mode (enhanced)
        adapter = SchemaAdapter(schema, use_ocr_grounding=True)
        signature = adapter.get_dspy_signature()
        program = dspy.Predict(signature)
    """

    def __init__(self, schema: ExtractionSchema, use_ocr_grounding: bool = False):
        """
        Initialize SchemaAdapter

        Args:
            schema: ExtractionSchema defining fields
            use_ocr_grounding: If True, signatures will include OCR text input
        """
        self.schema = schema
        self.use_ocr_grounding = use_ocr_grounding
        self._extraction_model = None
        self._dspy_signature = None

    def get_extraction_model(self) -> Type[BaseModel]:
        """Get or create the Pydantic extraction model"""
        if self._extraction_model is None:
            self._extraction_model = create_pydantic_model_from_schema(self.schema)
        return self._extraction_model

    def get_dspy_signature(self) -> Type[dspy.Signature]:
        """Get or create the DSPy signature"""
        if self._dspy_signature is None:
            extraction_model = self.get_extraction_model()
            self._dspy_signature = create_dspy_signature_from_schema(
                self.schema,
                extraction_model,
                use_ocr_grounding=self.use_ocr_grounding
            )
        return self._dspy_signature

    def create_dspy_program(self) -> dspy.Module:
        """Create a DSPy program (Predict module) for this schema"""
        signature = self.get_dspy_signature()
        return dspy.Predict(signature)


# Example usage
if __name__ == "__main__":
    from services.models.schema import ExtractionSchema, FieldDefinition, FieldType

    # Example: Receipt schema
    receipt_schema = ExtractionSchema(
        version=1,
        fields=[
            FieldDefinition(
                name="before_tax_total",
                display_name="Before-Tax Total",
                description="Subtotal before taxes",
                data_type=FieldType.CURRENCY,
                required=True
            ),
            FieldDefinition(
                name="after_tax_total",
                display_name="After-Tax Total",
                description="Final total with taxes",
                data_type=FieldType.CURRENCY,
                required=True
            )
        ]
    )

    # Create adapter
    adapter = SchemaAdapter(receipt_schema)

    # Get components
    extraction_model = adapter.get_extraction_model()
    dspy_signature = adapter.get_dspy_signature()
    dspy_program = adapter.create_dspy_program()

    print("✓ Pydantic Model:", extraction_model.__name__)
    print("✓ DSPy Signature:", dspy_signature.__name__)
    print("✓ DSPy Program:", type(dspy_program).__name__)
    print("\nSignature Instruction:")
    print(dspy_signature.__doc__)
