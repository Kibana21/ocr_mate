"""
Test GEPA Service with Receipt Data

This script demonstrates using the reusable GEPA service
with the same receipt data from gepa_receipt_optimization.py
"""

import os
from dotenv import load_dotenv

from services.models import (
    ExtractionSchema,
    FieldDefinition,
    FieldType,
    GroundTruthExample,
    OptimizationConfig,
    LLMConfig
)
from services.gepa import GEPAOptimizer

# Load environment variables
load_dotenv()


def create_receipt_schema() -> ExtractionSchema:
    """Create the receipt extraction schema"""
    return ExtractionSchema(
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


def create_receipt_ground_truth() -> list[GroundTruthExample]:
    """Create ground truth examples (same as gepa_receipt_optimization.py)"""
    return [
        GroundTruthExample(
            document_path='images/receipts/IMG_2171.jpg',
            labeled_values={'before_tax_total': 25.0, 'after_tax_total': 25.30}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2170.jpg',
            labeled_values={'before_tax_total': 246.62, 'after_tax_total': 258.96}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2172.jpg',
            labeled_values={'before_tax_total': 80.0, 'after_tax_total': 88.8}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2166.jpg',
            labeled_values={'before_tax_total': 559.93, 'after_tax_total': 561.64}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2167.jpg',
            labeled_values={'before_tax_total': 195.0, 'after_tax_total': 232.92}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2173.jpg',
            labeled_values={'before_tax_total': 2805, 'after_tax_total': 3394.06}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2163.jpg',
            labeled_values={'before_tax_total': 1660.0, 'after_tax_total': 2134.0}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2160.jpg',
            labeled_values={'before_tax_total': 2011.0, 'after_tax_total': 2521.61}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2174.jpg',
            labeled_values={'before_tax_total': 9520.00, 'after_tax_total': 10576.00}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2175.jpg',
            labeled_values={'before_tax_total': 1315.00, 'after_tax_total': 1381.00}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2169.jpg',
            labeled_values={'before_tax_total': 1265.00, 'after_tax_total': 1530.65}
        ),
        GroundTruthExample(
            document_path='images/receipts/IMG_2168.jpg',
            labeled_values={'before_tax_total': 2011.00, 'after_tax_total': 2522.00}
        ),
    ]


def create_optimization_config(test_mode: bool = True) -> OptimizationConfig:
    """Create optimization configuration"""
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        raise ValueError("GEMINI_API_KEY not found in environment")

    return OptimizationConfig(
        student_llm=LLMConfig(
            provider="gemini",
            model_name="gemini-2.0-flash-exp",
            api_key=gemini_key,
            temperature=0
        ),
        reflection_llm=LLMConfig(
            provider="gemini",
            model_name="gemini-2.0-flash-exp",
            api_key=gemini_key,
            temperature=0
        ),
        delay_seconds=10.0,  # Conservative delay to avoid rate limits
        test_mode=test_mode   # Set to False for full 12-receipt optimization
    )


def main():
    """Run GEPA optimization on receipts"""
    print("\n🎯 Testing GEPA Service with Receipt Data")
    print("=" * 80)
    print()

    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠ Error: GEMINI_API_KEY not set")
        print("  Please set it in your .env file")
        return

    # Create schema
    print("[1/4] Creating receipt schema...")
    schema = create_receipt_schema()
    print(f"  ✓ Schema created with {len(schema.fields)} fields")

    # Create ground truth
    print("\n[2/4] Loading ground truth examples...")
    ground_truth = create_receipt_ground_truth()
    print(f"  ✓ Loaded {len(ground_truth)} examples")

    # Create config
    print("\n[3/4] Creating optimization config...")
    TEST_MODE = True  # Change to False for full optimization
    config = create_optimization_config(test_mode=TEST_MODE)
    if TEST_MODE:
        print(f"  ⚠ TEST MODE: Will use only 4 receipts")
    print(f"  ✓ Config created")
    print(f"    - Student LLM: {config.student_llm.provider}/{config.student_llm.model_name}")
    print(f"    - Reflection LLM: {config.reflection_llm.provider}/{config.reflection_llm.model_name}")
    print(f"    - Delay: {config.delay_seconds}s between API calls")

    # Run optimization
    print("\n[4/4] Running GEPA optimization...")
    print()

    optimizer = GEPAOptimizer(
        schema=schema,
        config=config,
        output_dir="optimized_pipelines/receipts"
    )

    result = optimizer.optimize(ground_truth)

    # Print results
    print("\n" + "=" * 80)
    if result.success:
        print("✓ SUCCESS!")
        print("=" * 80)
        print(f"\nBaseline Accuracy: {result.metrics.baseline_accuracy * 100:.1f}%")
        print(f"Optimized Accuracy: {result.metrics.optimized_accuracy * 100:.1f}%")
        print(f"Improvement: {result.metrics.improvement:+.1f}%")
        print(f"\nOptimization Time: {result.metrics.optimization_time_seconds:.1f}s")
        print(f"Training Examples: {result.metrics.training_examples_used}")
        print(f"Validation Examples: {result.metrics.validation_examples_used}")
        print(f"\nOptimized Pipeline: {result.optimized_program_path}")
    else:
        print("✗ FAILED")
        print("=" * 80)
        print(f"\nError: {result.error_message}")

    print("\n" + "=" * 80)
    print("\n💡 Next Steps:")
    print("  1. Review the optimized pipeline")
    print("  2. Test on new receipts")
    print("  3. Use this same service for OTHER document types (invoices, contracts, etc.)")
    print()


if __name__ == "__main__":
    main()
