"""
Metric Factory - Generic GEPA-compatible metrics with feedback

Creates evaluation metrics that work with any schema and provide
textual feedback for GEPA's reflective optimization.
"""

import dspy
from typing import Any, Dict, Optional
from services.models.schema import ExtractionSchema, FieldDefinition, FieldType


def compare_field_values(expected: Any, actual: Any, field_def: FieldDefinition) -> bool:
    """
    Compare two field values considering data type.

    Args:
        expected: Ground truth value
        actual: Predicted value
        field_def: Field definition with type info

    Returns:
        True if values match (with type-appropriate tolerance)
    """
    # Handle None cases
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    # Type-specific comparison
    if field_def.data_type in [FieldType.NUMBER, FieldType.CURRENCY]:
        # Numeric comparison with small tolerance for floating point
        try:
            expected_float = float(expected)
            actual_float = float(actual)
            return abs(expected_float - actual_float) < 0.01
        except (ValueError, TypeError):
            return False

    elif field_def.data_type == FieldType.BOOLEAN:
        # Boolean comparison
        return bool(expected) == bool(actual)

    else:
        # String comparison (case-insensitive for most fields)
        expected_str = str(expected).strip().lower()
        actual_str = str(actual).strip().lower()
        return expected_str == actual_str


def generate_field_feedback(
    field_name: str,
    field_def: FieldDefinition,
    expected: Any,
    actual: Any,
    is_correct: bool
) -> str:
    """
    Generate specific feedback for a field extraction.

    Args:
        field_name: Name of the field
        field_def: Field definition
        expected: Ground truth value
        actual: Predicted value
        is_correct: Whether extraction was correct

    Returns:
        Textual feedback string
    """
    if is_correct:
        return f"{field_def.display_name} extracted correctly: {actual}"

    # Generate error-specific feedback
    feedback_parts = []

    feedback_parts.append(
        f"{field_def.display_name} incorrect. "
        f"Expected: {expected}, Got: {actual or 'None'}."
    )

    # Add field-specific hints
    if field_def.extraction_hints:
        feedback_parts.append("Extraction hints:")
        for hint in field_def.extraction_hints:
            feedback_parts.append(f"  • {hint}")

    # Add type-specific guidance
    if field_def.data_type == FieldType.CURRENCY:
        feedback_parts.append(
            "For currency fields, look for dollar signs ($) or other currency symbols. "
            "Remove commas and convert to decimal number."
        )
    elif field_def.data_type == FieldType.DATE:
        feedback_parts.append(
            "For date fields, convert to ISO format (YYYY-MM-DD). "
            "Look for common date labels like 'Date:', 'Date Issued:', etc."
        )
    elif field_def.data_type == FieldType.NUMBER:
        feedback_parts.append(
            "For numeric fields, extract only the number without units or symbols."
        )

    return " ".join(feedback_parts)


def create_metric_function(schema: ExtractionSchema):
    """
    Create a GEPA-compatible metric function for a specific schema.

    The metric function has the 5-parameter signature required by GEPA:
    (gold, pred, trace=None, pred_name=None, pred_trace=None)

    Args:
        schema: ExtractionSchema defining fields

    Returns:
        Metric function compatible with GEPA optimizer
    """

    def metric_with_feedback(gold, pred, trace=None, pred_name=None, pred_trace=None):
        """
        GEPA-compatible metric with 5 parameters and textual feedback.

        Args:
            gold: Ground truth dspy.Example
            pred: Prediction
            trace: Legacy parameter (may be None)
            pred_name: Name of predictor (optional) - when provided, returns feedback
            pred_trace: Detailed trace with reasoning (optional)

        Returns:
            - If pred_name is None: returns float score
            - If pred_name is specified: returns dspy.Prediction(score=float, feedback=str)
        """
        # Extract the data objects
        gold_data = gold.extracted_data if hasattr(gold, 'extracted_data') else gold
        pred_data = pred.extracted_data if hasattr(pred, 'extracted_data') else pred

        # Compare each field
        correct_fields = 0
        total_fields = len(schema.fields)
        field_results = []

        for field_def in schema.fields:
            field_name = field_def.name

            # Get values
            try:
                expected_value = getattr(gold_data, field_name, None)
                actual_value = getattr(pred_data, field_name, None)
            except AttributeError:
                # Handle dict-like access
                expected_value = gold_data.get(field_name) if isinstance(gold_data, dict) else None
                actual_value = pred_data.get(field_name) if isinstance(pred_data, dict) else None

            # Compare
            is_correct = compare_field_values(expected_value, actual_value, field_def)

            if is_correct:
                correct_fields += 1

            # Generate feedback for this field
            feedback = generate_field_feedback(
                field_name,
                field_def,
                expected_value,
                actual_value,
                is_correct
            )

            field_results.append({
                'field': field_name,
                'correct': is_correct,
                'feedback': feedback
            })

        # Calculate overall score
        score = float(correct_fields / total_fields) if total_fields > 0 else 0.0

        # If no specific predictor feedback requested, return just the score
        if pred_name is None:
            return score

        # Generate comprehensive feedback for GEPA
        feedback_lines = []

        if score == 1.0:
            feedback_lines.append("✓ All fields extracted correctly! Excellent work.")
        else:
            feedback_lines.append(
                f"⚠ {correct_fields}/{total_fields} fields correct ({score*100:.0f}% accuracy). "
                f"Errors in {total_fields - correct_fields} field(s)."
            )
            feedback_lines.append("")
            feedback_lines.append("Field-by-field analysis:")

            for result in field_results:
                status = "✓" if result['correct'] else "✗"
                feedback_lines.append(f"{status} {result['feedback']}")

        # Add general extraction tips
        if score < 1.0:
            feedback_lines.append("")
            feedback_lines.append("General tips:")
            feedback_lines.append("• Look for clear labels near the values")
            feedback_lines.append("• Check both header and footer sections")
            feedback_lines.append("• Be precise with number formatting")

        combined_feedback = "\n".join(feedback_lines)

        return dspy.Prediction(score=score, feedback=combined_feedback)

    return metric_with_feedback


# Example usage
if __name__ == "__main__":
    from services.models.schema import ExtractionSchema, FieldDefinition, FieldType

    # Example schema
    receipt_schema = ExtractionSchema(
        version=1,
        fields=[
            FieldDefinition(
                name="before_tax_total",
                display_name="Before-Tax Total",
                description="Subtotal before taxes",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=["Look for 'Subtotal' label"]
            ),
            FieldDefinition(
                name="after_tax_total",
                display_name="After-Tax Total",
                description="Final total with taxes",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=["Look for 'Total' at bottom"]
            )
        ]
    )

    # Create metric
    metric = create_metric_function(receipt_schema)

    # Test with mock data
    class MockData:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    gold = MockData(extracted_data=MockData(before_tax_total=25.0, after_tax_total=25.30))
    pred = MockData(extracted_data=MockData(before_tax_total=25.0, after_tax_total=25.30))

    # Test score-only mode
    score = metric(gold, pred)
    print(f"Score (no feedback): {score}")

    # Test feedback mode
    result = metric(gold, pred, pred_name="test_predictor")
    print(f"\nScore with feedback: {result.score}")
    print(f"Feedback:\n{result.feedback}")
