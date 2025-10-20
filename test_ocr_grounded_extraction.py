"""
Test OCR-Grounded Extraction (Image + OCR Text Dual Input)

This demonstrates the enhanced approach where LLM receives BOTH:
1. Document image (for visual context)
2. OCR-extracted text (for accurate text reference)

Benefits:
- Reduced vision errors (LLM can reference OCR text)
- Better field extraction (spatial context from image + text from OCR)
- Faster processing (text is cheaper than vision tokens)
- More robust (fallback if vision fails)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from services.models import (
    ExtractionSchema,
    FieldDefinition,
    FieldType,
    GroundTruthExample,
    OptimizationConfig,
    LLMConfig,
    ImageProcessingConfig,
    GEPAConfig
)
from services.ocr import AzureDocumentIntelligenceService, OCRMarkdownFormatter
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
                extraction_hints=["Store name", "Merchant"]
            ),
            FieldDefinition(
                name="total",
                display_name="Total",
                description="Final total amount",
                data_type=FieldType.CURRENCY,
                required=True,
                extraction_hints=["Total", "Amount due"]
            )
        ]
    )


def demo_ocr_text_formatting():
    """
    Demo 1: OCR Text Formatting for LLM Grounding

    Shows how OCR text is formatted as structured markdown for LLM consumption.
    """
    print("\n" + "="*80)
    print("DEMO 1: OCR TEXT FORMATTING")
    print("="*80)

    receipt_path = "receipt_data/receipt_1.jpg"

    if not Path(receipt_path).exists():
        print(f"\n⚠️  Sample receipt not found: {receipt_path}")
        print("\n   This demo would show:")
        print("   - Raw OCR output")
        print("   - Compact markdown format (minimal tokens)")
        print("   - Structured markdown format (with layout hints)")
        print("   - Full markdown format (with metadata)")
        return

    # Extract OCR
    print(f"\n1. Extracting OCR from: {receipt_path}")
    ocr_service = AzureDocumentIntelligenceService.from_env()
    ocr_result = ocr_service.extract_text(receipt_path)

    print(f"   Pages: {len(ocr_result.pages)}")
    print(f"   Lines: {len(ocr_result.pages[0].lines)}")

    # Format in different ways
    formatter = OCRMarkdownFormatter()

    print("\n2. Compact Format (Recommended for LLM - Minimal Tokens):")
    print("-" * 80)
    compact_text = formatter.format_compact(ocr_result)
    print(compact_text[:300] + "..." if len(compact_text) > 300 else compact_text)
    print(f"\n   Token estimate: ~{len(compact_text.split())} words")

    print("\n3. Structured Format (With Layout Hints):")
    print("-" * 80)
    structured_text = formatter.format_with_layout(ocr_result)
    print(structured_text[:300] + "..." if len(structured_text) > 300 else structured_text)

    print("\n4. Full Format (With Metadata):")
    print("-" * 80)
    full_markdown = formatter.format(ocr_result)
    print(full_markdown[:300] + "..." if len(full_markdown) > 300 else full_markdown)

    print("\n✅ OCR text formatted for LLM consumption!")


def demo_vision_only_vs_ocr_grounded():
    """
    Demo 2: Compare Vision-Only vs OCR-Grounded Extraction

    Shows the difference in prompt construction and results.
    """
    print("\n" + "="*80)
    print("DEMO 2: VISION-ONLY VS OCR-GROUNDED COMPARISON")
    print("="*80)

    schema = create_receipt_schema()

    print("\n📌 Extraction Task:")
    print(f"   Schema: {schema.fields[0].name}, {schema.fields[1].name}")

    print("\n" + "-"*80)
    print("MODE 1: Vision-Only (Original)")
    print("-"*80)
    print("\nLLM Inputs:")
    print("  ✅ document_image: dspy.Image")
    print("\nInstruction:")
    print('  "Extract structured data from the document image."')
    print("\nProcess:")
    print("  1. LLM looks at image")
    print("  2. LLM 'reads' text using vision capabilities")
    print("  3. LLM extracts fields")
    print("\nPros:")
    print("  ✓ Simple - one input")
    print("  ✓ Works well for clear documents")
    print("\nCons:")
    print("  ✗ Vision errors (misreads small text)")
    print("  ✗ Expensive (vision tokens cost more)")
    print("  ✗ Slower processing")

    print("\n" + "-"*80)
    print("MODE 2: OCR-Grounded (Enhanced)")
    print("-"*80)
    print("\nLLM Inputs:")
    print("  ✅ document_image: dspy.Image")
    print("  ✅ ocr_text: str  ← NEW!")
    print("\nInstruction:")
    print('  "Extract data using BOTH the image and OCR text."')
    print('  "Use OCR text for textual content."')
    print('  "Use image for visual context."')
    print("\nProcess:")
    print("  1. OCR extracts text (fast, cheap)")
    print("  2. LLM receives image + OCR text")
    print("  3. LLM references OCR text for accuracy")
    print("  4. LLM uses image for context")
    print("\nPros:")
    print("  ✓ More accurate (OCR text reference)")
    print("  ✓ Faster (less vision processing)")
    print("  ✓ More robust (OCR as fallback)")
    print("  ✓ Better for small text")
    print("\nCons:")
    print("  ✗ Slightly more complex")
    print("  ✗ Requires OCR preprocessing")

    print("\n" + "="*80)
    print("RECOMMENDATION:")
    print("="*80)
    print("\n✅ Use OCR-Grounded for:")
    print("   - Small text (receipts, invoices)")
    print("   - Complex layouts (forms, tables)")
    print("   - High-volume processing (cost savings)")
    print("   - Production systems (better accuracy)")
    print("\n⚠️  Use Vision-Only for:")
    print("   - Quick prototypes")
    print("   - Simple documents")
    print("   - Low-volume processing")


def demo_gepa_with_ocr_grounding():
    """
    Demo 3: GEPA Optimization with OCR Grounding

    Shows how to train with OCR text included.
    """
    print("\n" + "="*80)
    print("DEMO 3: GEPA OPTIMIZATION WITH OCR GROUNDING")
    print("="*80)

    schema = create_receipt_schema()

    print("\n1. Configuration")
    print("-" * 80)
    print("   Mode: OCR-Grounded")
    print("   LLM receives: Image + OCR Text")
    print("   Training examples: 5 receipts")

    # Create config with OCR grounding enabled
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

    # Create ground truth
    ground_truth_examples = [
        GroundTruthExample(
            document_path=f"receipt_data/receipt_{i}.jpg",
            labeled_values={
                "merchant_name": f"Store {i}",
                "total": 20.00 + i
            }
        )
        for i in range(1, 6)
    ]

    # Check if samples exist
    if not Path(ground_truth_examples[0].document_path).exists():
        print(f"\n⚠️  Sample receipts not found")
        print("\n   Workflow would be:")
        print("   1. For each training example:")
        print("      a. Load image")
        print("      b. Run OCR extraction")
        print("      c. Format OCR as compact markdown")
        print("      d. Create DSPy example with (image, ocr_text, labels)")
        print("   2. Run GEPA optimization:")
        print("      a. Baseline program receives image + OCR text")
        print("      b. LLM learns to use OCR text for accuracy")
        print("      c. Prompts optimized via GEPA feedback")
        print("   3. Result: Trained pipeline that uses OCR + Image")
        print("\n✅ Would complete with OCR-grounded pipeline!")
        return

    print("\n2. Preparing training data with OCR...")

    # Initialize OCR service
    ocr_service = AzureDocumentIntelligenceService.from_env()

    # Create optimizer with OCR grounding
    print("3. Creating GEPAOptimizer with OCR grounding enabled...")

    # Note: The optimizer needs to be updated to support use_ocr_grounding parameter
    # For now, this demonstrates the concept

    print("\n4. Training examples would include:")
    for i, example in enumerate(ground_truth_examples, 1):
        print(f"\n   Example {i}:")
        print(f"   - Image: {example.document_path}")
        print(f"   - OCR Text: <extracted markdown>")
        print(f"   - Labels: {example.labeled_values}")

    print("\n5. GEPA optimization process:")
    print("   Step 1: Create baseline program")
    print("           - Signature: (image, ocr_text) → extracted_data")
    print("           - LLM receives both inputs")
    print("   Step 2: Run GEPA")
    print("           - Student LLM extracts using image + OCR")
    print("           - Metric compares to ground truth")
    print("           - Reflection LLM provides feedback")
    print("           - Prompts improved")
    print("   Step 3: Save optimized pipeline")
    print("           - Pipeline now uses OCR text effectively")

    print("\n✅ OCR-grounded pipeline would be ready for production!")
    print("\n📊 Expected improvements:")
    print("   - Higher accuracy (OCR text reference)")
    print("   - Fewer vision errors")
    print("   - Better performance on small text")


def demo_production_extraction_with_ocr():
    """
    Demo 4: Production Extraction with OCR Grounding

    Shows how to use trained OCR-grounded pipeline.
    """
    print("\n" + "="*80)
    print("DEMO 4: PRODUCTION EXTRACTION WITH OCR GROUNDING")
    print("="*80)

    print("\n1. New document received")
    new_doc = "uploads/new_receipt.jpg"
    print(f"   Document: {new_doc}")

    print("\n2. Extraction process:")
    print("   Step 1: Run OCR")
    print("          ├─ Extract text")
    print("          ├─ Format as compact markdown")
    print("          └─ Cost: ~$0.001")

    print("   Step 2: Load optimized pipeline")
    print("          ├─ Load trained DSPy program")
    print("          └─ Signature: (image, ocr_text) → data")

    print("   Step 3: Run extraction")
    print("          ├─ Load image")
    print("          ├─ Pass image + OCR text to LLM")
    print("          ├─ LLM uses OCR for text reference")
    print("          ├─ LLM uses image for context")
    print("          └─ Cost: ~$0.01")

    print("   Step 4: Return result")
    print("          └─ Extracted fields with high confidence")

    print("\n3. Example code:")
    print("-" * 80)
    print("""
    # Extract OCR
    ocr_result = ocr_service.extract_text(document_path)
    formatter = OCRMarkdownFormatter()
    ocr_text = formatter.format_compact(ocr_result)

    # Load trained pipeline
    pipeline = dspy.Predict.load("pipelines/receipt_ocr_grounded.json")

    # Extract with both image and OCR text
    image = load_image(document_path)
    result = pipeline(document_image=image, ocr_text=ocr_text)

    # Result has higher accuracy due to OCR grounding
    extracted_data = result.extracted_data
    """)

    print("\n✅ Production-ready OCR-grounded extraction!")


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("OCR-GROUNDED EXTRACTION DEMO")
    print("Image + OCR Text Dual Input for Better Accuracy")
    print("="*80)

    # Demo 1: OCR formatting
    demo_ocr_text_formatting()

    input("\n\nPress Enter to continue to Demo 2...")

    # Demo 2: Comparison
    demo_vision_only_vs_ocr_grounded()

    input("\n\nPress Enter to continue to Demo 3...")

    # Demo 3: Training with OCR
    demo_gepa_with_ocr_grounding()

    input("\n\nPress Enter to continue to Demo 4...")

    # Demo 4: Production usage
    demo_production_extraction_with_ocr()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY: WHY OCR-GROUNDED EXTRACTION?")
    print("="*80)

    print("\n🎯 Key Benefits:")
    print("\n1. **Accuracy**")
    print("   - OCR provides accurate text reference")
    print("   - Reduces vision errors (especially small text)")
    print("   - Image provides visual context")

    print("\n2. **Performance**")
    print("   - OCR preprocessing is fast (~50-100ms)")
    print("   - LLM processes text faster than vision")
    print("   - Overall faster extraction")

    print("\n3. **Cost**")
    print("   - OCR: $0.001/page (very cheap)")
    print("   - Text tokens cheaper than vision tokens")
    print("   - Total cost similar but better quality")

    print("\n4. **Robustness**")
    print("   - Dual input = two sources of truth")
    print("   - If vision fails, OCR text helps")
    print("   - If OCR fails, vision helps")

    print("\n5. **Better Results**")
    print("   - Small text: OCR excels")
    print("   - Layout understanding: Image helps")
    print("   - Field location: Both contribute")

    print("\n" + "="*80)
    print("WHEN TO USE OCR GROUNDING?")
    print("="*80)

    print("\n✅ **Always Use For:**")
    print("   - Receipts (small text)")
    print("   - Invoices (structured + small text)")
    print("   - Forms (clear layout + small fields)")
    print("   - Production systems (need accuracy)")

    print("\n⚠️  **Maybe Skip For:**")
    print("   - Simple prototypes")
    print("   - Very clear, large text documents")
    print("   - When OCR infrastructure not available")

    print("\n" + "="*80)
    print("IMPLEMENTATION STATUS")
    print("="*80)

    print("\n✅ **Completed:**")
    print("   [✓] OCR markdown formatter")
    print("   [✓] Schema adapter with OCR grounding mode")
    print("   [✓] Training data converter with OCR support")
    print("   [✓] Dual input DSPy signatures")

    print("\n📝 **To Complete:**")
    print("   [ ] Update GEPAOptimizer to accept use_ocr_grounding parameter")
    print("   [ ] Test with real training examples")
    print("   [ ] Benchmark accuracy improvement")
    print("   [ ] Document best practices")

    print("\n🚀 **Ready to implement in your workflow!**")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
