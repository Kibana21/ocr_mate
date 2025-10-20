"""
Test script demonstrating OCR-assisted annotation and dual extraction verification

This script demonstrates the complete enhanced workflow:
1. OCR-assisted ground truth annotation
2. GEPA optimization with verified ground truth
3. Dual extraction verification (OCR + LLM) on new documents
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.models import (
    ExtractionSchema,
    FieldDefinition,
    FieldType,
    GroundTruthExample,
    OptimizationConfig,
    LLMConfig,
    ImageProcessingConfig,
    GEPAConfig,
    DocumentAnnotation,
    OCRAssistedAnnotationService,
    ConflictResolutionStrategy,
    DualExtractionVerifier
)
from services.ocr import AzureDocumentIntelligenceService
from services.gepa import GEPAOptimizer


def create_receipt_schema() -> ExtractionSchema:
    """Create schema for receipt extraction"""
    return ExtractionSchema(
        version=1,
        fields=[
            FieldDefinition(
                name="merchant_name",
                display_name="Merchant Name",
                description="Name of the store or merchant",
                data_type=FieldType.TEXT,
                required=True,
                extraction_hints=["Store name", "Merchant", "Company name at top"]
            ),
            FieldDefinition(
                name="transaction_date",
                display_name="Transaction Date",
                description="Date of purchase",
                data_type=FieldType.DATE,
                required=True,
                extraction_hints=["Date", "Transaction date", "Purchase date"]
            ),
            FieldDefinition(
                name="subtotal",
                display_name="Subtotal",
                description="Amount before tax",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=["Subtotal", "Before tax", "Pre-tax total"]
            ),
            FieldDefinition(
                name="tax",
                display_name="Tax",
                description="Tax amount",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=["Tax", "Sales tax", "GST", "VAT"]
            ),
            FieldDefinition(
                name="total",
                display_name="Total",
                description="Final total amount",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=["Total", "Amount due", "Final total", "Grand total"]
            )
        ]
    )


def demo_ocr_assisted_annotation():
    """
    Demo 1: OCR-Assisted Ground Truth Annotation

    This demonstrates how OCR can pre-fill annotation values for users.
    """
    print("\n" + "="*80)
    print("DEMO 1: OCR-ASSISTED GROUND TRUTH ANNOTATION")
    print("="*80)

    # Setup
    schema = create_receipt_schema()
    ocr_service = AzureDocumentIntelligenceService.from_env()
    annotation_service = OCRAssistedAnnotationService(ocr_service)

    # Simulate: User uploads first receipt for annotation
    receipt_path = "receipt_data/receipt_1.jpg"

    if not Path(receipt_path).exists():
        print(f"\n⚠️  Sample receipt not found: {receipt_path}")
        print("   This demo requires sample receipt images.")
        print("\n   Workflow would be:")
        print("   1. User uploads document")
        print("   2. System runs OCR extraction")
        print("   3. System pre-fills form with OCR values")
        print("   4. User reviews and corrects values")
        print("   5. User clicks 'Save' to create ground truth")
        return None

    print(f"\n1. User uploads document: {receipt_path}")

    # Run OCR-assisted annotation
    print("2. System runs OCR and pre-fills form...")
    annotation = annotation_service.create_annotation(receipt_path, schema)

    print("\n3. OCR Pre-filled Values (shown in UI form):")
    print("-" * 80)
    for field_annotation in annotation.annotations:
        print(f"   {field_annotation.field_name}: {field_annotation.value}")
        print(f"      Source: {field_annotation.source}")
        print(f"      OCR Confidence: {field_annotation.ocr_confidence}")
        print(f"      User Verified: {field_annotation.user_verified} ❌")
        print()

    # Simulate: User reviews and corrects one value
    print("4. User reviews form and corrects 'total' value:")
    print("   Changed: $25.47 → $25.99")
    from services.models.annotation import AnnotationSource
    annotation.set_field_value(
        field_name="total",
        value=25.99,
        source=AnnotationSource.USER_EDITED
    )

    # Simulate: User marks other fields as verified
    print("\n5. User clicks ✓ to verify other fields:")
    for field_annotation in annotation.annotations:
        if field_annotation.field_name != "total":
            annotation.mark_field_verified(field_annotation.field_name)
            print(f"   ✓ {field_annotation.field_name} verified")

    # Check completion status
    print("\n6. Check annotation completion:")
    status = annotation.get_completion_status(schema)
    print(f"   Annotated: {status['annotated_fields']}/{status['total_fields']}")
    print(f"   Verified: {status['verified_fields']}/{status['total_fields']}")
    print(f"   Complete: {status['is_complete']} ✓")

    # Convert to ground truth
    print("\n7. Save as ground truth for GEPA training:")
    ground_truth = annotation.to_ground_truth()
    print(f"   {ground_truth}")

    print("\n✅ OCR-assisted annotation complete!")
    print("   User only needed to correct 1 field instead of typing all 5!")

    return annotation


def demo_gepa_with_ocr_annotations():
    """
    Demo 2: GEPA Optimization with OCR-Assisted Ground Truth

    This demonstrates training with ground truth created via OCR assistance.
    """
    print("\n" + "="*80)
    print("DEMO 2: GEPA OPTIMIZATION WITH OCR-ASSISTED GROUND TRUTH")
    print("="*80)

    print("\n1. User has annotated 5 receipts using OCR assistance")
    print("   (In real scenario, these would come from database)")

    # Simulate: User has annotated 5 receipts
    # (In reality, these would be DocumentAnnotation objects converted to GroundTruthExample)
    ground_truth_examples = [
        GroundTruthExample(
            document_path=f"receipt_data/receipt_{i}.jpg",
            labeled_values={
                "merchant_name": f"Store {i}",
                "transaction_date": "2024-01-15",
                "subtotal": 20.00 + i,
                "tax": 1.50 + (i * 0.1),
                "total": 21.50 + i + (i * 0.1)
            }
        )
        for i in range(1, 6)
    ]

    print(f"\n2. Ground truth examples: {len(ground_truth_examples)}")

    print("\n3. User clicks 'Optimize Pipeline' button")
    print("   (This would trigger GEPA optimization in background)")

    # Check if sample data exists
    if not Path(ground_truth_examples[0].document_path).exists():
        print(f"\n⚠️  Sample receipts not found")
        print("   In production, GEPA would:")
        print("   - Train extraction pipeline on ground truth")
        print("   - Optimize prompts using GEPA")
        print("   - Save optimized pipeline for production use")
        print("\n✅ Optimization would complete in background!")
        return None

    # Run GEPA optimization (with test mode for speed)
    schema = create_receipt_schema()
    config = OptimizationConfig(
        student_llm=LLMConfig(
            provider="gemini",
            model_name="gemini-2.0-flash-exp",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0
        ),
        reflection_llm=LLMConfig(
            provider="gemini",
            model_name="gemini-2.0-flash-exp",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        ),
        gepa=GEPAConfig(
            auto=1,
            num_threads=1,
            reflection_minibatch_size=2,
            track_stats=True
        ),
        image_processing=ImageProcessingConfig(),
        delay_seconds=2.0,
        test_mode=True
    )

    print("\n   Running GEPA optimization...")
    optimizer = GEPAOptimizer(schema, config, output_dir="optimized_pipelines/receipts")

    try:
        result = optimizer.optimize(ground_truth_examples)

        print("\n4. Optimization Results:")
        print(f"   Baseline Accuracy: {result.metrics.baseline_accuracy:.1%}")
        print(f"   Optimized Accuracy: {result.metrics.optimized_accuracy:.1%}")
        print(f"   Improvement: {result.metrics.improvement_percentage:.1f}%")
        print(f"   Optimized pipeline saved: {result.artifacts.get('saved_path')}")

        print("\n✅ Pipeline optimized and ready for production!")
        return result

    except Exception as e:
        print(f"\n⚠️  Optimization error: {e}")
        print("   (Likely missing API keys or sample data)")
        return None


def demo_dual_extraction_verification():
    """
    Demo 3: Dual Extraction Verification (OCR + LLM)

    This demonstrates production extraction with counter-verification.
    """
    print("\n" + "="*80)
    print("DEMO 3: DUAL EXTRACTION VERIFICATION (PRODUCTION)")
    print("="*80)

    print("\n1. User uploads new receipt for processing")

    # Check if we have optimized pipeline and sample data
    receipt_path = "receipt_data/new_receipt.jpg"

    if not Path(receipt_path).exists():
        print(f"\n⚠️  Sample receipt not found: {receipt_path}")
        print("\n   Workflow would be:")
        print("   1. User uploads new document")
        print("   2. System runs OCR extraction (fast baseline)")
        print("   3. System runs LLM extraction (trained pipeline)")
        print("   4. System compares OCR vs LLM results")
        print("   5. System resolves conflicts and provides confidence scores")
        print("   6. High-confidence results auto-approved")
        print("   7. Low-confidence results flagged for human review")
        return None

    # Check for optimized pipeline
    optimized_pipeline_path = "optimized_pipelines/receipts/pipeline_optimized_latest.json"
    if not Path(optimized_pipeline_path).exists():
        print(f"\n⚠️  Optimized pipeline not found: {optimized_pipeline_path}")
        print("   Run demo_gepa_with_ocr_annotations() first to create pipeline")
        return None

    print(f"   Document: {receipt_path}")

    # Load optimized pipeline
    print("\n2. Loading optimized extraction pipeline...")
    import dspy
    llm_extractor = dspy.Predict.load(optimized_pipeline_path)

    # Setup verification service
    print("3. Setting up dual extraction verifier...")
    ocr_service = AzureDocumentIntelligenceService.from_env()
    verifier = DualExtractionVerifier(
        ocr_service=ocr_service,
        llm_extractor=llm_extractor,
        conflict_strategy=ConflictResolutionStrategy.HIGHER_CONFIDENCE,
        human_review_threshold=0.6
    )

    # Run verification
    print("\n4. Running dual extraction (OCR + LLM)...")
    schema = create_receipt_schema()

    try:
        verification = verifier.verify_extraction(receipt_path, schema)

        print("\n5. Verification Results:")
        print("-" * 80)

        for fv in verification.field_verifications:
            print(f"\n   Field: {fv.field_name}")
            print(f"   OCR Value: {fv.ocr_value} (confidence: {fv.ocr_confidence:.2f})")
            print(f"   LLM Value: {fv.llm_value} (confidence: {fv.llm_confidence:.2f})")
            print(f"   Status: {fv.status}")

            if fv.status.value == "match":
                print(f"   ✓ MATCH - Final: {fv.final_value} (confidence: {fv.confidence_score:.2f})")
            elif fv.status.value == "mismatch":
                print(f"   ⚠️  CONFLICT - {fv.conflict_reason}")
                print(f"   Resolution: {fv.resolution_method} → {fv.final_value}")
                print(f"   Confidence: {fv.confidence_score:.2f}")

        print("\n" + "-" * 80)
        print(f"\n   Overall Confidence: {verification.overall_confidence:.1%}")
        print(f"   Match Rate: {verification.match_rate:.1%}")
        print(f"   Needs Human Review: {'YES ⚠️' if verification.needs_human_review else 'NO ✓'}")

        if verification.needs_human_review:
            print("\n   Low confidence fields (need review):")
            for field_name in verification.get_low_confidence_fields():
                print(f"   - {field_name}")

        print("\n6. Final Extraction:")
        final_extraction = verification.get_final_extraction()
        for field_name, value in final_extraction.items():
            print(f"   {field_name}: {value}")

        print("\n✅ Dual extraction verification complete!")

        return verification

    except Exception as e:
        print(f"\n⚠️  Verification error: {e}")
        print("   (Likely missing API keys or sample data)")
        return None


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("OCR-ENHANCED EXTRACTION WORKFLOW DEMO")
    print("="*80)
    print("\nThis demo shows three key enhancements:")
    print("1. OCR-assisted ground truth annotation (reduces manual typing)")
    print("2. GEPA optimization with verified ground truth")
    print("3. Dual extraction verification (OCR + LLM for confidence)")

    # Demo 1: OCR-assisted annotation
    annotation = demo_ocr_assisted_annotation()

    # Demo 2: GEPA optimization
    input("\n\nPress Enter to continue to Demo 2...")
    optimization_result = demo_gepa_with_ocr_annotations()

    # Demo 3: Dual verification
    input("\n\nPress Enter to continue to Demo 3...")
    verification = demo_dual_extraction_verification()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY: BENEFITS OF OCR INTEGRATION")
    print("="*80)
    print("\n✅ Ground Truth Annotation:")
    print("   - OCR pre-fills form → User only corrects mistakes")
    print("   - 80% time savings for annotation")
    print("   - Fewer user typing errors")

    print("\n✅ Production Extraction:")
    print("   - Dual extraction provides confidence scores")
    print("   - OCR + LLM agreement → High confidence (auto-approve)")
    print("   - OCR vs LLM conflict → Lower confidence (human review)")
    print("   - Better quality control and error detection")

    print("\n✅ Cost Optimization:")
    print("   - OCR for baseline (cheap, fast)")
    print("   - LLM for accuracy (expensive, smart)")
    print("   - Best of both worlds!")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
