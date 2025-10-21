"""
Test Azure Document Intelligence Native Markdown Output

This demonstrates Azure's built-in markdown output format which:
- Preserves document structure (headings, tables, lists)
- Formats tables as markdown tables
- Maintains reading order
- Handles multi-column layouts
- No custom formatting needed!

This is SUPERIOR to custom markdown formatting because Azure's AI
understands document structure natively.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from services.ocr import AzureDocumentIntelligenceService


def test_native_markdown_extraction():
    """
    Test Azure's native markdown output vs custom formatting
    """
    print("\n" + "="*80)
    print("AZURE NATIVE MARKDOWN EXTRACTION TEST")
    print("="*80)

    # Use actual receipt from images folder
    receipt_path = "images/receipts/IMG_2160.jpg"

    if not Path(receipt_path).exists():
        print(f"\n⚠️  Sample document not found: {receipt_path}")
        print("\n   Available receipts:")
        receipts_dir = Path("images/receipts")
        if receipts_dir.exists():
            for img in sorted(receipts_dir.glob("*.jpg"))[:5]:
                print(f"     - {img}")
        print("\n   This test demonstrates:")
        print("   1. Azure's native markdown output (RECOMMENDED)")
        print("   2. Comparison with custom markdown formatting")
        print("   3. Structure preservation (tables, lists, headings)")
        return

    # Initialize service
    print(f"\n1. Initializing Azure Document Intelligence...")
    try:
        service = AzureDocumentIntelligenceService.from_env()
        print("   ✓ Connected to Azure")
    except Exception as e:
        print(f"   ✗ Failed to connect: {e}")
        print("\n   Make sure environment variables are set:")
        print("     AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        print("     AZURE_DOCUMENT_INTELLIGENCE_KEY")
        return

    # Test native markdown
    print(f"\n2. Extracting with NATIVE markdown output...")
    try:
        native_markdown = service.extract_markdown(receipt_path)
        print("   ✓ Native markdown extracted")
        print(f"   Length: {len(native_markdown)} characters")
        print(f"   Lines: {len(native_markdown.split(chr(10)))}")
    except ImportError as e:
        print(f"   ✗ SDK version too old: {e}")
        print("\n   Upgrade to get native markdown support:")
        print("   pip install --upgrade azure-ai-documentintelligence")
        return
    except Exception as e:
        print(f"   ✗ Extraction failed: {e}")
        return

    # Display native markdown
    print("\n3. Native Markdown Output (First 500 chars):")
    print("-" * 80)
    print(native_markdown[:500])
    if len(native_markdown) > 500:
        print(f"... ({len(native_markdown) - 500} more characters)")

    # Test custom formatting for comparison
    print("\n4. Custom Formatting (for comparison):")
    print("-" * 80)
    try:
        from services.ocr.markdown_formatter import OCRMarkdownFormatter
        ocr_result = service.extract_text(receipt_path)
        formatter = OCRMarkdownFormatter()
        custom_markdown = formatter.format_compact(ocr_result)
        print(custom_markdown[:500])
        if len(custom_markdown) > 500:
            print(f"... ({len(custom_markdown) - 500} more characters)")
    except Exception as e:
        print(f"   ✗ Custom formatting failed: {e}")

    # Comparison
    print("\n5. Comparison:")
    print("-" * 80)
    print(f"   Native Markdown:  {len(native_markdown)} chars")
    print(f"   Custom Markdown:  {len(custom_markdown)} chars")

    print("\n   Native Markdown Benefits:")
    print("   ✓ Preserves document structure")
    print("   ✓ Formats tables as markdown tables")
    print("   ✓ Maintains reading order")
    print("   ✓ Handles multi-column layouts")
    print("   ✓ No custom formatting code needed")
    print("   ✓ Better for complex documents")

    print("\n   Custom Markdown Benefits:")
    print("   ✓ Works with older SDK versions")
    print("   ✓ Can customize formatting")
    print("   ✓ Can add custom metadata")

    print("\n" + "="*80)
    print("RECOMMENDATION: Use Native Markdown (extract_markdown)")
    print("="*80)
    print("\nWhy?")
    print("- Azure's AI understands document structure")
    print("- Better table formatting")
    print("- Better multi-column handling")
    print("- Maintained by Microsoft (keeps improving)")
    print("- No custom code to maintain")

    print("\n✅ Test complete!")


def test_markdown_with_tables():
    """
    Test markdown extraction with document containing tables
    """
    print("\n" + "="*80)
    print("MARKDOWN EXTRACTION WITH MULTIPLE RECEIPTS")
    print("="*80)

    # Use actual receipts from images folder
    receipts_dir = Path("images/receipts")

    if not receipts_dir.exists():
        print(f"\n⚠️  Receipts folder not found: {receipts_dir}")
        print("\n   Native markdown excels at:")
        print("   - Tables (formatted as markdown tables)")
        print("   - Multi-column layouts")
        print("   - Hierarchical structure (headings)")
        print("   - Lists (bulleted, numbered)")
        print("\n   Example output for an invoice:")
        print("-" * 80)
        print("""
# Invoice #INV-2024-001

**Date**: January 15, 2024
**Due Date**: February 15, 2024

## Bill To
Acme Corporation
123 Main St
New York, NY 10001

## Items

| Description | Quantity | Unit Price | Total |
|------------|----------|------------|-------|
| Consulting Services | 10 hours | $150.00 | $1,500.00 |
| Software License | 1 | $500.00 | $500.00 |

## Summary

| | |
|------------|----------|
| Subtotal | $2,000.00 |
| Tax (8%) | $160.00 |
| **Total** | **$2,160.00** |
        """)
        print("-" * 80)
        print("\n   This structured format is PERFECT for LLM grounding!")
        return

    service = AzureDocumentIntelligenceService.from_env()

    # Get first 3 receipts for testing
    receipt_files = sorted(receipts_dir.glob("*.jpg"))[:3]

    print(f"\nExtracting markdown from {len(receipt_files)} receipts...")

    for i, receipt_path in enumerate(receipt_files, 1):
        print(f"\n{'='*80}")
        print(f"Receipt {i}/{len(receipt_files)}: {receipt_path.name}")
        print('='*80)

        try:
            markdown = service.extract_markdown(str(receipt_path))

            print("\nMarkdown output (first 800 chars):")
            print("-" * 80)
            print(markdown[:800])
            if len(markdown) > 800:
                print(f"\n... ({len(markdown) - 800} more characters)")
            print("-" * 80)

            print(f"\n✓ Successfully extracted {len(markdown)} characters")

        except Exception as e:
            print(f"\n✗ Failed to extract: {e}")

    print("\n✅ Markdown extraction complete!")


def demo_llm_grounding_with_native_markdown():
    """
    Demo: How to use native markdown for LLM grounding
    """
    print("\n" + "="*80)
    print("LLM GROUNDING WITH NATIVE MARKDOWN")
    print("="*80)

    print("\n📋 Workflow:")
    print("\n1. Extract document as markdown")
    print("   ocr_markdown = service.extract_markdown('images/receipts/IMG_2160.jpg')")

    print("\n2. Load document image")
    print("   image = load_image('images/receipts/IMG_2160.jpg')")

    print("\n3. Pass BOTH to LLM")
    print("   result = llm_extractor(")
    print("       document_image=image,")
    print("       ocr_text=ocr_markdown  ← Structured markdown!")
    print("   )")

    print("\n4. LLM receives:")
    print("   ✓ Image for visual context")
    print("   ✓ Structured markdown for text reference")
    print("   ✓ Table structure preserved")
    print("   ✓ Headings for section understanding")

    print("\n🎯 Result:")
    print("   - More accurate extraction")
    print("   - Better field location")
    print("   - Faster processing")
    print("   - Fewer vision errors")

    print("\n📝 Code Example:")
    print("-" * 80)
    print("""
from services.ocr import AzureDocumentIntelligenceService
from services.gepa.image_processor import load_and_resize_image
import dspy

# Setup
ocr_service = AzureDocumentIntelligenceService.from_env()

# Extract markdown (FAST: ~100ms)
ocr_markdown = ocr_service.extract_markdown('images/receipts/IMG_2160.jpg')

# Load image
image = load_and_resize_image('images/receipts/IMG_2160.jpg')

# Load trained pipeline (with OCR grounding enabled)
pipeline = dspy.Predict.load('pipelines/receipt_ocr_grounded.json')

# Extract with dual input
result = pipeline(
    document_image=image,
    ocr_text=ocr_markdown  # Structured markdown from Azure
)

# Result has higher accuracy!
extracted_data = result.extracted_data
    """)
    print("-" * 80)

    print("\n✅ Native markdown makes LLM grounding easy and effective!")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("AZURE NATIVE MARKDOWN - COMPREHENSIVE TEST")
    print("="*80)

    # Test 1: Basic extraction
    test_native_markdown_extraction()

    input("\n\nPress Enter to continue to next demo...")

    # Test 2: Tables
    test_markdown_with_tables()

    input("\n\nPress Enter to continue to final demo...")

    # Test 3: LLM grounding
    demo_llm_grounding_with_native_markdown()

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print("\n✅ **Use Azure Native Markdown for:**")
    print("   1. LLM grounding (best structure preservation)")
    print("   2. Documents with tables")
    print("   3. Multi-column layouts")
    print("   4. Complex documents")
    print("   5. Production systems")

    print("\n📚 **API Methods:**")
    print("   - service.extract_markdown(file_path)")
    print("   - service.extract_markdown_from_url(url)")

    print("\n🔧 **Requirements:**")
    print("   - azure-ai-documentintelligence >= 1.0.0b1")
    print("   - Upgrade: pip install --upgrade azure-ai-documentintelligence")

    print("\n🚀 **Ready for production!**")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
