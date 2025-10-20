# OCR Integration Guide: Azure Document Intelligence

## Overview

This guide explains how Azure Document Intelligence (OCR) integrates with the GEPA optimization service to provide two key enhancements:

1. **OCR-Assisted Ground Truth Annotation** - Pre-fill annotation forms to reduce manual typing
2. **Dual Extraction Verification** - Use OCR + LLM together for confidence scoring and quality control

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    OCR MATE PLATFORM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 1: Ground Truth Creation (Annotation UI)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│   User uploads document                                          │
│         ↓                                                         │
│   Azure OCR extracts text                                        │
│         ↓                                                         │
│   System pre-fills form with OCR values                         │
│         ↓                                                         │
│   User reviews & corrects                                        │
│         ↓                                                         │
│   Ground Truth Example saved                                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 2: GEPA Optimization                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│   Ground Truth Examples (3-5 annotated docs)                    │
│         ↓                                                         │
│   GEPA Optimizer trains extraction pipeline                     │
│         ↓                                                         │
│   Optimized LLM pipeline saved                                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 3: Production Extraction (with Verification)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│   New document uploaded                                          │
│         ↓                                                         │
│   ┌──────────────────────┐  ┌───────────────────────────┐      │
│   │ OCR Extraction       │  │ LLM Extraction            │      │
│   │ (Fast, Structured)   │  │ (Smart, Trained)          │      │
│   └──────────────────────┘  └───────────────────────────┘      │
│         ↓                              ↓                         │
│         └──────────────┬───────────────┘                         │
│                        ↓                                          │
│              Dual Extraction Verifier                            │
│              (Compare OCR vs LLM)                                │
│                        ↓                                          │
│              ┌─────────┴─────────┐                               │
│              ↓                   ↓                                │
│         Match (High Conf)   Conflict (Low Conf)                 │
│         Auto-approve         Human review                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Use Case 1: OCR-Assisted Ground Truth Annotation

### Problem
Creating ground truth examples for GEPA training is tedious:
- Users must manually type values from documents
- Prone to typing errors
- Time-consuming (especially for 20+ field schemas)

### Solution
Use OCR to pre-fill the annotation form, users only correct mistakes.

### Implementation

#### Step 1: User Uploads Document

```python
# User clicks "Upload" in UI
document_path = "uploads/invoice_001.pdf"
```

#### Step 2: System Runs OCR Pre-fill

```python
from services.ocr import AzureDocumentIntelligenceService
from services.models import OCRAssistedAnnotationService

# Initialize services
ocr_service = AzureDocumentIntelligenceService.from_env()
annotation_service = OCRAssistedAnnotationService(ocr_service)

# Create OCR-assisted annotation
annotation = annotation_service.create_annotation(
    document_path=document_path,
    schema=invoice_schema  # User's defined schema
)

# annotation.annotations contains pre-filled values from OCR
```

#### Step 3: Display Pre-filled Form in UI

```javascript
// Frontend (React/Vue)
// Display form with OCR pre-filled values

{annotation.annotations.map(field => (
  <FormField key={field.field_name}>
    <label>{field.field_name}</label>
    <input
      value={field.value}  // Pre-filled from OCR
      onChange={handleEdit}  // User can correct
    />
    <span className={field.ocr_confidence > 0.8 ? 'high-conf' : 'low-conf'}>
      OCR Confidence: {field.ocr_confidence}
    </span>
    <button onClick={() => verifyField(field.field_name)}>
      ✓ Verify
    </button>
  </FormField>
))}
```

#### Step 4: User Reviews and Corrects

```python
# Backend: User corrects a value
from services.models.annotation import AnnotationSource

annotation.set_field_value(
    field_name="invoice_total",
    value=1599.99,  # User corrected value
    source=AnnotationSource.USER_EDITED
)

# User confirms other fields are correct
annotation.mark_field_verified("invoice_number")
annotation.mark_field_verified("invoice_date")
# ... etc
```

#### Step 5: Save as Ground Truth

```python
# Check if annotation is complete
status = annotation.get_completion_status(invoice_schema)
if status['is_complete']:
    # Convert to ground truth for GEPA training
    ground_truth = GroundTruthExample(
        document_path=annotation.document_path,
        labeled_values=annotation.to_ground_truth()
    )

    # Save to database
    db.save_ground_truth(ground_truth)
```

### Benefits

✅ **80% Time Savings**: User only corrects mistakes instead of typing everything
✅ **Fewer Errors**: No user typing mistakes
✅ **Better UX**: Instant pre-fill feels responsive
✅ **Confidence Indicators**: Low OCR confidence → User pays extra attention

---

## Use Case 2: Dual Extraction Verification

### Problem
How do we know if LLM extraction is correct in production?
- No ground truth for new documents
- Can't trust LLM blindly
- Need confidence scores for quality control

### Solution
Run both OCR and LLM extraction, compare results, generate confidence scores.

### Implementation

#### Step 1: Setup Verifier

```python
from services.ocr import AzureDocumentIntelligenceService
from services.models import DualExtractionVerifier, ConflictResolutionStrategy
import dspy

# Load optimized pipeline (from GEPA training)
llm_extractor = dspy.Predict.load("optimized_pipelines/invoices/pipeline.json")

# Setup OCR service
ocr_service = AzureDocumentIntelligenceService.from_env()

# Create verifier
verifier = DualExtractionVerifier(
    ocr_service=ocr_service,
    llm_extractor=llm_extractor,
    conflict_strategy=ConflictResolutionStrategy.HIGHER_CONFIDENCE,
    human_review_threshold=0.6  # Below 60% confidence → human review
)
```

#### Step 2: Process New Document

```python
# User uploads new invoice for processing
document_path = "uploads/new_invoice.pdf"

# Run dual extraction
verification = verifier.verify_extraction(
    document_path=document_path,
    schema=invoice_schema
)
```

#### Step 3: Review Verification Results

```python
# Check overall confidence
print(f"Overall Confidence: {verification.overall_confidence:.1%}")
print(f"Match Rate: {verification.match_rate:.1%}")
print(f"Needs Review: {verification.needs_human_review}")

# Get conflicts
conflicts = verification.get_conflicts()
for field in conflicts:
    print(f"Conflict in {field.field_name}:")
    print(f"  OCR: {field.ocr_value} (conf: {field.ocr_confidence})")
    print(f"  LLM: {field.llm_value} (conf: {field.llm_confidence})")
    print(f"  Final: {field.final_value} (resolved by {field.resolution_method})")
```

#### Step 4: Handle Based on Confidence

```python
if verification.overall_confidence >= 0.9:
    # High confidence → Auto-approve
    final_extraction = verification.get_final_extraction()
    db.save_extraction(document_path, final_extraction, status="approved")

elif verification.overall_confidence >= 0.6:
    # Medium confidence → Auto-save but flag for spot check
    final_extraction = verification.get_final_extraction()
    db.save_extraction(document_path, final_extraction, status="needs_spot_check")

else:
    # Low confidence → Human review required
    conflicts = verification.get_conflicts()
    db.save_extraction(document_path, None, status="needs_review", conflicts=conflicts)
    notify_human_reviewer(document_path, conflicts)
```

### Conflict Resolution Strategies

#### 1. `HIGHER_CONFIDENCE` (Recommended Default)
Choose the extraction with higher confidence score.

```python
verifier = DualExtractionVerifier(
    conflict_strategy=ConflictResolutionStrategy.HIGHER_CONFIDENCE
)

# Example:
# OCR: $1,234.56 (confidence: 0.7)
# LLM: $1,234.50 (confidence: 0.9)
# Result: $1,234.50 (chose LLM due to higher confidence)
```

#### 2. `PREFER_LLM`
Always prefer LLM value (useful if LLM is highly trained).

```python
verifier = DualExtractionVerifier(
    conflict_strategy=ConflictResolutionStrategy.PREFER_LLM
)

# Always returns LLM value, regardless of confidence
```

#### 3. `PREFER_OCR`
Always prefer OCR value (useful for simple structured documents).

```python
verifier = DualExtractionVerifier(
    conflict_strategy=ConflictResolutionStrategy.PREFER_OCR
)

# Always returns OCR value, useful when OCR is very reliable
```

#### 4. `WEIGHTED_AVERAGE` (For Numeric Fields)
Compute weighted average based on confidence scores.

```python
verifier = DualExtractionVerifier(
    conflict_strategy=ConflictResolutionStrategy.WEIGHTED_AVERAGE
)

# Example:
# OCR: $1,200 (confidence: 0.7)
# LLM: $1,300 (confidence: 0.9)
# Result: (1200*0.7 + 1300*0.9) / (0.7 + 0.9) = $1,256.25
```

#### 5. `HUMAN_REVIEW`
Don't resolve conflicts automatically, always flag for human review.

```python
verifier = DualExtractionVerifier(
    conflict_strategy=ConflictResolutionStrategy.HUMAN_REVIEW
)

# Sets final_value = None, confidence = 0.0 for all conflicts
```

### Benefits

✅ **Confidence Scores**: Know when to trust extractions
✅ **Quality Control**: Catch LLM hallucinations by comparing with OCR
✅ **Cost Optimization**: OCR (cheap) + LLM (expensive) = balanced approach
✅ **Audit Trail**: Both OCR and LLM values stored for debugging
✅ **Smart Routing**: High confidence → auto-approve, Low confidence → human review

---

## Field-Level Verification Logic

### How Values Are Compared

```python
# services/models/verification.py

def _values_match(value1, value2, field_type):
    """Type-aware value comparison"""

    # Exact match
    if value1 == value2:
        return True

    # Normalized string match
    if str(value1).strip().lower() == str(value2).strip().lower():
        return True

    # Type-specific matching
    if field_type in [CURRENCY, NUMBER]:
        # Allow 1% tolerance for numeric fields
        # "$1,234.56" matches "$1,234.50" if within 1%
        num1 = parse_number(value1)
        num2 = parse_number(value2)
        return abs(num1 - num2) / max(num1, num2) < 0.01

    if field_type == DATE:
        # Normalize date formats
        # "01/15/2024" matches "2024-01-15"
        date1 = parse_date(value1)
        date2 = parse_date(value2)
        return date1 == date2

    return False
```

### Confidence Calculation

```python
# Match → Boost confidence
if ocr_value == llm_value:
    confidence = min(ocr_confidence, llm_confidence) + 0.15
    # Both agree → increase confidence by 15%

# Mismatch → Choose higher confidence
else:
    if llm_confidence >= ocr_confidence:
        confidence = llm_confidence
    else:
        confidence = ocr_confidence

# Single source → Slightly lower confidence
if only_ocr:
    confidence = ocr_confidence * 0.8
    # Only one source → decrease confidence by 20%
```

---

## API Integration Examples

### FastAPI Endpoints

```python
# backend/api/routes.py

from fastapi import FastAPI, UploadFile, HTTPException
from services.ocr import AzureDocumentIntelligenceService
from services.models import OCRAssistedAnnotationService, DualExtractionVerifier

app = FastAPI()

# Endpoint 1: OCR-assisted annotation
@app.post("/api/annotations/create")
async def create_annotation(
    file: UploadFile,
    schema_id: str
):
    """Create OCR-assisted annotation for uploaded document"""

    # Save uploaded file
    file_path = save_upload(file)

    # Get schema from database
    schema = db.get_schema(schema_id)

    # Create OCR-assisted annotation
    ocr_service = AzureDocumentIntelligenceService.from_env()
    annotation_service = OCRAssistedAnnotationService(ocr_service)

    annotation = annotation_service.create_annotation(file_path, schema)

    # Save to database
    annotation_id = db.save_annotation(annotation)

    return {
        "annotation_id": annotation_id,
        "annotations": annotation.annotations,
        "ocr_full_text": annotation.ocr_full_text,
        "completion_status": annotation.get_completion_status(schema)
    }


# Endpoint 2: Update annotation field
@app.put("/api/annotations/{annotation_id}/fields/{field_name}")
async def update_field(
    annotation_id: str,
    field_name: str,
    value: Any,
    source: str  # "user_edited" or "user_manual"
):
    """User corrects an annotation field"""

    annotation = db.get_annotation(annotation_id)

    annotation.set_field_value(
        field_name=field_name,
        value=value,
        source=AnnotationSource(source)
    )

    db.save_annotation(annotation)

    return {"status": "updated"}


# Endpoint 3: Verify field
@app.post("/api/annotations/{annotation_id}/fields/{field_name}/verify")
async def verify_field(annotation_id: str, field_name: str):
    """User confirms OCR value is correct"""

    annotation = db.get_annotation(annotation_id)
    annotation.mark_field_verified(field_name)
    db.save_annotation(annotation)

    return {"status": "verified"}


# Endpoint 4: Production extraction with verification
@app.post("/api/extractions/process")
async def process_document(
    file: UploadFile,
    schema_id: str,
    use_verification: bool = True
):
    """Process new document with optional dual extraction verification"""

    file_path = save_upload(file)
    schema = db.get_schema(schema_id)

    if use_verification:
        # Load optimized pipeline
        pipeline = load_optimized_pipeline(schema_id)

        # Setup verifier
        ocr_service = AzureDocumentIntelligenceService.from_env()
        verifier = DualExtractionVerifier(
            ocr_service=ocr_service,
            llm_extractor=pipeline,
            conflict_strategy=ConflictResolutionStrategy.HIGHER_CONFIDENCE
        )

        # Run verification
        verification = verifier.verify_extraction(file_path, schema)

        return {
            "extraction": verification.get_final_extraction(),
            "confidence": verification.overall_confidence,
            "match_rate": verification.match_rate,
            "needs_review": verification.needs_human_review,
            "conflicts": [
                {
                    "field": fv.field_name,
                    "ocr_value": fv.ocr_value,
                    "llm_value": fv.llm_value,
                    "final_value": fv.final_value
                }
                for fv in verification.get_conflicts()
            ]
        }

    else:
        # Simple LLM extraction only
        pipeline = load_optimized_pipeline(schema_id)
        result = pipeline(document_image=load_image(file_path))

        return {
            "extraction": result.extracted_data.dict()
        }
```

---

## Configuration

### Environment Variables

```bash
# .env

# Azure Document Intelligence (OCR)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_api_key_here

# LLM for extraction
GEMINI_API_KEY=your_gemini_key
# or
OPENAI_API_KEY=your_openai_key
```

### Azure Document Intelligence Models

Choose the right model for your use case:

```python
# Fast text extraction only
ocr_result = ocr_service.extract_text(
    document_path,
    model_id="prebuilt-read"  # Fastest, text only
)

# Text + layout (tables, structure)
ocr_result = ocr_service.extract_text(
    document_path,
    model_id="prebuilt-layout"  # Good for forms, tables
)

# Text + key-value pairs
ocr_result = ocr_service.extract_text(
    document_path,
    model_id="prebuilt-document"  # Extracts form fields automatically
)

# Specialized models
# - prebuilt-invoice (for invoices)
# - prebuilt-receipt (for receipts)
# - prebuilt-idDocument (for IDs, passports)
```

---

## Cost Optimization Strategies

### Strategy 1: OCR-First for Simple Documents

For highly structured documents (standardized forms, receipts):

```python
# Use OCR only, skip expensive LLM
ocr_result = ocr_service.extract_text(document_path, model_id="prebuilt-receipt")
extraction = simple_parser(ocr_result)  # Simple rule-based extraction

# Cost: ~$0.001 per page (OCR only)
```

### Strategy 2: LLM-Only for Complex Documents

For unstructured documents (contracts, reports):

```python
# Use vision LLM only, skip OCR
extraction = llm_pipeline(document_image=image)

# Cost: ~$0.01-0.05 per page (LLM vision)
```

### Strategy 3: Hybrid with Smart Routing

```python
# Route based on document complexity
if document_is_structured(document_path):
    # Simple → OCR only
    extraction = ocr_extraction(document_path)
    confidence = 0.85
else:
    # Complex → Dual extraction
    verification = dual_extraction_verification(document_path)
    extraction = verification.get_final_extraction()
    confidence = verification.overall_confidence

# Average cost: ~$0.003-0.02 per page (optimized)
```

### Strategy 4: Batch Processing with OCR Caching

```python
# Cache OCR results for reuse
ocr_cache = {}

def process_document(document_path):
    # Run OCR once, cache result
    if document_path not in ocr_cache:
        ocr_cache[document_path] = ocr_service.extract_text(document_path)

    ocr_result = ocr_cache[document_path]

    # Use cached OCR for multiple extraction attempts
    # (e.g., during GEPA optimization iterations)
    extraction = llm_pipeline_with_ocr_text(ocr_result.full_text)

    return extraction
```

---

## Testing

Run the comprehensive test suite:

```bash
cd /Users/kartik/Documents/Work/Projects/ocr_mate/ocr_mate

# Test OCR service
python -c "
from services.ocr import AzureDocumentIntelligenceService
ocr = AzureDocumentIntelligenceService.from_env()
result = ocr.extract_text('receipt_data/receipt_1.jpg')
print(result.full_text)
"

# Test full workflow
python test_ocr_verification.py
```

---

## Summary

### When to Use OCR

| Use Case | Use OCR? | Why |
|----------|----------|-----|
| **Ground Truth Annotation** | ✅ Always | Saves 80% of typing time |
| **Production Extraction (Simple Docs)** | ✅ OCR Only | Cost-effective for structured documents |
| **Production Extraction (Complex Docs)** | ✅ With LLM | Dual extraction for confidence scoring |
| **GEPA Training** | ❌ No | Train on ground truth only (user-verified) |

### Architecture Decision

We built **TWO integration points** for OCR:

1. **Annotation Phase** (Always use OCR)
   - Pre-fill forms for users
   - Reduce manual typing
   - Faster ground truth creation

2. **Production Phase** (Optional use OCR)
   - Dual extraction for verification
   - Confidence scoring
   - Quality control

Both enhancements are **independent** and can be enabled/disabled separately!

---

## Next Steps

1. **Test with Real Data**: Run `test_ocr_verification.py` with your receipt images
2. **Tune Confidence Thresholds**: Adjust `human_review_threshold` based on your quality requirements
3. **Choose Conflict Strategy**: Pick the best `ConflictResolutionStrategy` for your use case
4. **Implement UI**: Build annotation interface with OCR pre-fill
5. **Monitor in Production**: Track match rates and confidence scores

---

## Support

For questions or issues:
- Review this guide
- Check `test_ocr_verification.py` for working examples
- See `services/ocr/azure_service.py` for OCR implementation
- See `services/models/verification.py` for verification logic
