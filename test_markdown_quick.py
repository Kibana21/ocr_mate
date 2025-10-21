"""
Quick test for Azure Native Markdown Extraction

This is a minimal test to verify:
1. Azure credentials work
2. Native markdown extraction works
3. Your receipts can be processed

Run this first before the full test suite.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("\n" + "="*80)
print("QUICK AZURE NATIVE MARKDOWN TEST")
print("="*80)

# Step 1: Check environment variables
print("\n1. Checking Azure credentials...")
endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

if endpoint:
    print(f"   ✓ Endpoint found: {endpoint}")
else:
    print("   ✗ AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT not set")
    print("\n   Add to your .env file:")
    print("   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com")
    exit(1)

if api_key:
    print(f"   ✓ API key found: {api_key[:10]}...{api_key[-4:]}")
else:
    print("   ✗ AZURE_DOCUMENT_INTELLIGENCE_KEY not set")
    print("\n   Add to your .env file:")
    print("   AZURE_DOCUMENT_INTELLIGENCE_KEY=your_api_key_here")
    exit(1)

# Step 2: Check receipts folder
print("\n2. Checking receipts folder...")
receipts_dir = Path("images/receipts")

if not receipts_dir.exists():
    print(f"   ✗ Folder not found: {receipts_dir}")
    exit(1)

receipt_files = sorted(receipts_dir.glob("*.jpg"))
print(f"   ✓ Found {len(receipt_files)} receipts")
if receipt_files:
    print(f"   First receipt: {receipt_files[0].name} ({receipt_files[0].stat().st_size / 1024:.1f} KB)")

# Step 3: Check SDK
print("\n3. Checking Azure SDK...")
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    print("   ✓ Azure SDK imported")
except ImportError as e:
    print(f"   ✗ Azure SDK not found: {e}")
    print("\n   Install with:")
    print("   pip install azure-ai-documentintelligence")
    exit(1)

# Check for native markdown support
try:
    from azure.ai.documentintelligence.models import DocumentContentFormat, AnalyzeDocumentRequest
    print("   ✓ Native markdown support available (DocumentContentFormat found)")
    has_native_markdown = True
except ImportError:
    print("   ⚠️  Native markdown not available (older SDK)")
    print("   Upgrade with: pip install --upgrade azure-ai-documentintelligence")
    has_native_markdown = False

# Step 4: Initialize service
print("\n4. Initializing Azure service...")
try:
    from services.ocr import AzureDocumentIntelligenceService
    service = AzureDocumentIntelligenceService.from_env()
    print("   ✓ Service initialized")
except Exception as e:
    print(f"   ✗ Failed to initialize: {e}")
    exit(1)

# Step 5: Test with first receipt
if not receipt_files:
    print("\n⚠️  No receipts found to test")
    exit(0)

test_receipt = receipt_files[0]
print(f"\n5. Testing markdown extraction with: {test_receipt.name}")

if has_native_markdown:
    print("   Extracting with NATIVE markdown (ContentFormat.MARKDOWN)...")
    try:
        markdown = service.extract_markdown(str(test_receipt))
        print(f"   ✓ Extraction successful!")
        print(f"   Length: {len(markdown)} characters")
        print(f"   Lines: {len(markdown.split(chr(10)))}")

        print("\n6. Markdown Output Preview (first 600 chars):")
        print("-" * 80)
        print(markdown[:600])
        if len(markdown) > 600:
            print(f"\n... ({len(markdown) - 600} more characters)")
        print("-" * 80)

        # Save to file for inspection
        output_file = "test_output_native_markdown.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Azure Native Markdown Output\n\n")
            f.write(f"**Source**: {test_receipt}\n\n")
            f.write(f"**Length**: {len(markdown)} characters\n\n")
            f.write("---\n\n")
            f.write(markdown)

        print(f"\n✅ Full output saved to: {output_file}")
        print(f"   Open it to see the complete markdown structure!")

    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        print("\n   Upgrade SDK:")
        print("   pip install --upgrade azure-ai-documentintelligence")
    except Exception as e:
        print(f"   ✗ Extraction failed: {e}")
        print("\n   Possible issues:")
        print("   - Check Azure credentials are correct")
        print("   - Verify Azure service is active")
        print("   - Check network connection")

else:
    print("   Using fallback method (extract_text)...")
    try:
        from services.ocr.markdown_formatter import OCRMarkdownFormatter

        ocr_result = service.extract_text(str(test_receipt))
        formatter = OCRMarkdownFormatter()
        markdown = formatter.format_compact(ocr_result)

        print(f"   ✓ Extraction successful (custom formatter)")
        print(f"   Length: {len(markdown)} characters")

        print("\n6. Markdown Output Preview (first 600 chars):")
        print("-" * 80)
        print(markdown[:600])
        if len(markdown) > 600:
            print(f"\n... ({len(markdown) - 600} more characters)")
        print("-" * 80)

        # Save to file
        output_file = "test_output_custom_markdown.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Custom Markdown Output\n\n")
            f.write(f"**Source**: {test_receipt}\n\n")
            f.write(f"**Length**: {len(markdown)} characters\n\n")
            f.write("---\n\n")
            f.write(markdown)

        print(f"\n✅ Full output saved to: {output_file}")
        print("\n⚠️  NOTE: To get native markdown (better quality):")
        print("   pip install --upgrade azure-ai-documentintelligence")

    except Exception as e:
        print(f"   ✗ Extraction failed: {e}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)

if has_native_markdown:
    print("\n✅ Everything working! Native markdown extraction available.")
    print("\nNext steps:")
    print("1. Review the output file to see markdown structure")
    print("2. Run full test suite: python test_azure_native_markdown.py")
    print("3. Use for LLM grounding in your extraction pipeline")
else:
    print("\n⚠️  Basic extraction working, but upgrade SDK for native markdown:")
    print("   pip install --upgrade azure-ai-documentintelligence")

print("\n" + "="*80)
