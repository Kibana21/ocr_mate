"""
Training Data Converter

Converts ground truth examples to DSPy format for GEPA optimization.
"""

import dspy
from typing import List, Type, Optional
from pydantic import BaseModel
from services.models.schema import GroundTruthExample, ExtractionSchema
from services.gepa.image_processor import load_and_resize_image


class TrainingDataConverter:
    """
    Converts ground truth examples to DSPy training format.

    Usage:
        # Vision-only mode
        converter = TrainingDataConverter(schema, extraction_model)
        dspy_examples = converter.convert(ground_truth_examples)

        # OCR-grounded mode
        converter = TrainingDataConverter(
            schema, extraction_model,
            ocr_service=ocr_service,
            use_ocr_grounding=True
        )
        dspy_examples = converter.convert(ground_truth_examples)
    """

    def __init__(
        self,
        schema: ExtractionSchema,
        extraction_model: Type[BaseModel],
        max_width: int = 512,
        max_height: int = 512,
        jpeg_quality: int = 60,
        ocr_service=None,  # AzureDocumentIntelligenceService
        use_ocr_grounding: bool = False
    ):
        """
        Initialize converter.

        Args:
            schema: ExtractionSchema defining fields
            extraction_model: Pydantic model for extracted data
            max_width: Max image width for processing
            max_height: Max image height for processing
            jpeg_quality: JPEG compression quality
            ocr_service: Optional OCR service for text extraction
            use_ocr_grounding: If True, include OCR text in training examples
        """
        self.schema = schema
        self.extraction_model = extraction_model
        self.max_width = max_width
        self.max_height = max_height
        self.jpeg_quality = jpeg_quality
        self.ocr_service = ocr_service
        self.use_ocr_grounding = use_ocr_grounding

    def convert_single(self, example: GroundTruthExample) -> dspy.Example:
        """
        Convert a single ground truth example to DSPy format.

        Args:
            example: GroundTruthExample with document path and labels

        Returns:
            dspy.Example ready for training
        """
        # Load and process image
        try:
            img = load_and_resize_image(
                example.document_path,
                max_width=self.max_width,
                max_height=self.max_height,
                jpeg_quality=self.jpeg_quality
            )
        except Exception as e:
            raise ValueError(
                f"Failed to load image {example.document_path}: {e}"
            )

        # Create extraction model instance with labeled values
        extracted_data = self.extraction_model(**example.labeled_values)

        # Create DSPy example
        if self.use_ocr_grounding and self.ocr_service:
            # OCR-grounded mode: Include OCR text (RECOMMENDED: Use native markdown)
            try:
                # Try Azure's native markdown output first (BEST for structure preservation)
                if hasattr(self.ocr_service, 'extract_markdown'):
                    ocr_text = self.ocr_service.extract_markdown(example.document_path)
                else:
                    # Fallback to custom formatter if native markdown not available
                    from services.ocr.markdown_formatter import OCRMarkdownFormatter
                    ocr_result = self.ocr_service.extract_text(example.document_path)
                    formatter = OCRMarkdownFormatter()
                    ocr_text = formatter.format_compact(ocr_result)
            except Exception as e:
                # Fallback to vision-only if OCR fails
                print(f"Warning: OCR failed for {example.document_path}: {e}")
                ocr_text = ""

            dspy_example = dspy.Example(
                document_image=img,
                ocr_text=ocr_text,
                extracted_data=extracted_data
            ).with_inputs("document_image", "ocr_text")
        else:
            # Vision-only mode (original)
            dspy_example = dspy.Example(
                document_image=img,
                extracted_data=extracted_data
            ).with_inputs("document_image")

        return dspy_example

    def convert(
        self,
        examples: List[GroundTruthExample],
        test_mode: bool = False
    ) -> List[dspy.Example]:
        """
        Convert multiple ground truth examples to DSPy format.

        Args:
            examples: List of GroundTruthExample objects
            test_mode: If True, only convert first 4 examples

        Returns:
            List of dspy.Example objects
        """
        # Limit examples in test mode
        if test_mode:
            examples = examples[:4]
            print(f"⚠ TEST MODE: Using only {len(examples)} examples")

        dspy_examples = []
        failed_examples = []

        for i, example in enumerate(examples, 1):
            try:
                dspy_example = self.convert_single(example)
                dspy_examples.append(dspy_example)
            except Exception as e:
                print(f"⚠ Warning: Failed to convert example {i}: {e}")
                failed_examples.append((example.document_path, str(e)))

        # Report results
        print(f"✓ Converted {len(dspy_examples)}/{len(examples)} examples successfully")
        if failed_examples:
            print(f"⚠ Failed examples:")
            for path, error in failed_examples:
                print(f"  - {path}: {error}")

        return dspy_examples

    def split_train_val(
        self,
        examples: List[dspy.Example],
        train_fraction: float = 0.8
    ) -> tuple[List[dspy.Example], List[dspy.Example]]:
        """
        Split examples into training and validation sets.

        Args:
            examples: List of DSPy examples
            train_fraction: Fraction for training (default 0.8)

        Returns:
            Tuple of (train_examples, val_examples)
        """
        split_idx = int(len(examples) * train_fraction)
        train_examples = examples[:split_idx]
        val_examples = examples[split_idx:]

        print(f"✓ Split: {len(train_examples)} training, {len(val_examples)} validation")

        return train_examples, val_examples


# Example usage
if __name__ == "__main__":
    from services.models.schema import ExtractionSchema, FieldDefinition, FieldType, GroundTruthExample
    from services.gepa.schema_adapter import SchemaAdapter

    # Example schema
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

    # Create extraction model
    adapter = SchemaAdapter(receipt_schema)
    extraction_model = adapter.get_extraction_model()

    # Example ground truth data
    ground_truth_examples = [
        GroundTruthExample(
            document_path='images/receipts/IMG_2171.jpg',
            labeled_values={'before_tax_total': 25.0, 'after_tax_total': 25.30}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2170.jpg',
            labeled_values={'before_tax_total': 246.62, 'after_tax_total': 258.96}
        ),
    ]

    # Convert
    converter = TrainingDataConverter(receipt_schema, extraction_model)

    try:
        dspy_examples = converter.convert(ground_truth_examples, test_mode=True)
        train, val = converter.split_train_val(dspy_examples)

        print(f"\n✓ Successfully created {len(dspy_examples)} DSPy examples")
        print(f"  Training: {len(train)}, Validation: {len(val)}")
    except Exception as e:
        print(f"⚠ Example not run (likely missing image files): {e}")
