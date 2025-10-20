# OCR Integration - Quick Reference Card

## 🚀 Quick Start

### Setup
```bash
# Install dependencies
pip install azure-ai-documentintelligence

# Set environment variables
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your_key"
```

### Test
```bash
python test_ocr_verification.py
```

---

## 📚 Common Use Cases

### Use Case 1: OCR-Assisted Annotation

```python
from services.ocr import AzureDocumentIntelligenceService
from services.models import OCRAssistedAnnotationService, AnnotationSource

# Initialize
ocr = AzureDocumentIntelligenceService.from_env()
service = OCRAssistedAnnotationService(ocr)

# Create annotation with OCR pre-fill
annotation = service.create_annotation("invoice.pdf", schema)

# User corrects value
annotation.set_field_value("total", 1599.99, AnnotationSource.USER_EDITED)

# User verifies other fields
annotation.mark_field_verified("invoice_number")

# Convert to ground truth
ground_truth = annotation.to_ground_truth()
```

**When to use**: Every time creating ground truth examples
**Benefit**: 80% time savings on annotation

---

### Use Case 2: Dual Extraction Verification

```python
from services.ocr import AzureDocumentIntelligenceService
from services.models import DualExtractionVerifier, ConflictResolutionStrategy
import dspy

# Load optimized pipeline
llm_extractor = dspy.Predict.load("pipelines/optimized.json")

# Setup verifier
ocr = AzureDocumentIntelligenceService.from_env()
verifier = DualExtractionVerifier(
    ocr_service=ocr,
    llm_extractor=llm_extractor,
    conflict_strategy=ConflictResolutionStrategy.HIGHER_CONFIDENCE,
    human_review_threshold=0.6
)

# Process document
verification = verifier.verify_extraction("new_invoice.pdf", schema)

# Check confidence
if verification.overall_confidence >= 0.9:
    extraction = verification.get_final_extraction()
    database.save(extraction, status="approved")
elif verification.needs_human_review:
    review_queue.add(verification.get_conflicts())
```

**When to use**: Production extraction for quality control
**Benefit**: Confidence scores + automatic error detection

---

## 🔧 Configuration Options

### OCR Models

```python
# Fast text only
ocr.extract_text(path, model_id="prebuilt-read")

# Text + layout (recommended)
ocr.extract_text(path, model_id="prebuilt-layout")

# Text + key-value pairs
ocr.extract_text(path, model_id="prebuilt-document")

# Specialized
ocr.extract_text(path, model_id="prebuilt-invoice")
ocr.extract_text(path, model_id="prebuilt-receipt")
```

### Conflict Resolution Strategies

```python
# Choose higher confidence (recommended)
ConflictResolutionStrategy.HIGHER_CONFIDENCE

# Always prefer LLM
ConflictResolutionStrategy.PREFER_LLM

# Always prefer OCR
ConflictResolutionStrategy.PREFER_OCR

# Weighted average (numeric fields)
ConflictResolutionStrategy.WEIGHTED_AVERAGE

# Always flag for review
ConflictResolutionStrategy.HUMAN_REVIEW
```

---

## 📊 Data Models

### DocumentAnnotation
```python
annotation = DocumentAnnotation(
    document_path="invoice.pdf",
    schema_version=1,
    annotations=[
        FieldAnnotation(
            field_name="total",
            value=1599.99,
            source=AnnotationSource.OCR_AUTO,
            ocr_confidence=0.85,
            user_verified=False
        )
    ],
    ocr_full_text="...",  # Full OCR text
    is_complete=False
)
```

### DocumentVerification
```python
verification = DocumentVerification(
    document_path="new_invoice.pdf",
    schema_version=1,
    field_verifications=[
        FieldVerification(
            field_name="total",
            ocr_value=1599.99,
            llm_value=1599.99,
            final_value=1599.99,
            status=VerificationStatus.MATCH,
            confidence_score=0.92,
            ocr_confidence=0.85,
            llm_confidence=0.92
        )
    ],
    overall_confidence=0.92,
    match_rate=1.0,
    needs_human_review=False
)
```

---

## 🎯 Decision Matrix

### When to Enable OCR?

| Scenario | Use OCR? | Why |
|----------|----------|-----|
| Creating ground truth | ✅ Always | Saves 80% typing time |
| Simple structured docs (production) | ✅ OCR only | Cost-effective |
| Complex docs (production) | ✅ OCR + LLM | Need confidence scores |
| Training pipeline | ❌ No | Use ground truth only |

### Which Conflict Strategy?

| Use Case | Strategy | When |
|----------|----------|------|
| General purpose | `HIGHER_CONFIDENCE` | Default, balanced |
| Highly trained LLM | `PREFER_LLM` | LLM is very accurate |
| Simple forms | `PREFER_OCR` | OCR is reliable enough |
| Financial data | `WEIGHTED_AVERAGE` | Need precision |
| High stakes | `HUMAN_REVIEW` | Manual verification required |

### Confidence Thresholds?

| Confidence | Action | Example |
|------------|--------|---------|
| ≥ 0.9 | Auto-approve | 90%+ confidence → trust it |
| 0.6 - 0.9 | Spot check | 60-89% → save but flag |
| < 0.6 | Human review | <60% → needs review |

---

## 🔍 Debugging

### Check OCR Output
```python
result = ocr.extract_text("document.pdf")
print(result.full_text)  # View extracted text
print(result.pages[0].lines)  # View lines with bounding boxes
```

### Inspect Annotation
```python
annotation = service.create_annotation("doc.pdf", schema)
for field in annotation.annotations:
    print(f"{field.field_name}: {field.value}")
    print(f"  Source: {field.source}")
    print(f"  OCR Confidence: {field.ocr_confidence}")
```

### Check Verification Details
```python
verification = verifier.verify_extraction("doc.pdf", schema)
for fv in verification.field_verifications:
    print(f"{fv.field_name}:")
    print(f"  OCR: {fv.ocr_value} ({fv.ocr_confidence})")
    print(f"  LLM: {fv.llm_value} ({fv.llm_confidence})")
    print(f"  Status: {fv.status}")
    if fv.status == VerificationStatus.MISMATCH:
        print(f"  Conflict: {fv.conflict_reason}")
        print(f"  Resolution: {fv.resolution_method}")
```

---

## 💰 Cost Estimates

### OCR (Azure Document Intelligence)
- `prebuilt-read`: $0.001/page
- `prebuilt-layout`: $0.010/page
- `prebuilt-invoice`: $0.010/page

### LLM Vision
- Gemini 2.0 Flash: ~$0.01/image
- GPT-4o: ~$0.03/image
- Claude 3.5: ~$0.05/image

### Example Monthly Costs (1000 docs)
- Vision only: $10-50/month
- OCR only: $1-10/month (lower accuracy)
- Dual (OCR + LLM): $11-60/month (with confidence)

---

## ⚠️ Common Pitfalls

### 1. Not Verifying OCR Annotations
```python
# ❌ Wrong: Save OCR values directly
ground_truth = annotation.to_ground_truth()  # Without user review!

# ✅ Right: User must verify first
if annotation.get_completion_status(schema)['is_complete']:
    ground_truth = annotation.to_ground_truth()
```

### 2. Wrong Confidence Threshold
```python
# ❌ Too strict: Everything goes to review
verifier = DualExtractionVerifier(human_review_threshold=0.95)

# ✅ Balanced: Most auto-approved, some review
verifier = DualExtractionVerifier(human_review_threshold=0.6)
```

### 3. Not Handling Conflicts
```python
# ❌ Wrong: Ignore conflicts
extraction = verification.get_final_extraction()  # May have low confidence!

# ✅ Right: Check confidence first
if verification.overall_confidence >= 0.9:
    extraction = verification.get_final_extraction()
else:
    handle_conflicts(verification.get_conflicts())
```

### 4. Wrong OCR Model
```python
# ❌ Overkill: Using expensive model for simple text
ocr.extract_text(doc, model_id="prebuilt-document")  # $0.01/page

# ✅ Efficient: Use appropriate model
ocr.extract_text(doc, model_id="prebuilt-read")  # $0.001/page
```

---

## 📖 Full Documentation

- **[OCR_INTEGRATION_GUIDE.md](./services/OCR_INTEGRATION_GUIDE.md)** - Comprehensive guide
- **[OCR_ENHANCEMENT_SUMMARY.md](./services/OCR_ENHANCEMENT_SUMMARY.md)** - Summary
- **[ARCHITECTURE_WITH_OCR.md](./ARCHITECTURE_WITH_OCR.md)** - Architecture diagrams
- **[test_ocr_verification.py](./test_ocr_verification.py)** - Working examples

---

## 🆘 Troubleshooting

### "Module not found: azure.ai.documentintelligence"
```bash
pip install azure-ai-documentintelligence
```

### "Missing Azure credentials"
```bash
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="..."
export AZURE_DOCUMENT_INTELLIGENCE_KEY="..."
```

### "Low OCR confidence"
- Use better quality images (300+ DPI)
- Try different OCR model (`prebuilt-layout` vs `prebuilt-read`)
- Check if document is rotated/skewed

### "Too many conflicts"
- Adjust `conflict_strategy` to `PREFER_LLM`
- Increase `human_review_threshold`
- Check if LLM is well-trained (run more GEPA iterations)

### "High costs"
- Use `prebuilt-read` instead of `prebuilt-layout`
- Cache OCR results for repeated processing
- Use OCR-only for simple documents (skip LLM)
- Batch process documents to amortize costs

---

## 🎓 Learning Path

1. **Start Here**: Read [OCR_ENHANCEMENT_SUMMARY.md](./services/OCR_ENHANCEMENT_SUMMARY.md)
2. **Understand Architecture**: Read [ARCHITECTURE_WITH_OCR.md](./ARCHITECTURE_WITH_OCR.md)
3. **Try Examples**: Run `python test_ocr_verification.py`
4. **Deep Dive**: Read [OCR_INTEGRATION_GUIDE.md](./services/OCR_INTEGRATION_GUIDE.md)
5. **Implement**: Build your own annotation UI and verification service

---

## ✅ Checklist: Adding OCR to Your Project

- [ ] Install `azure-ai-documentintelligence`
- [ ] Set environment variables (endpoint + key)
- [ ] Test OCR service: `ocr.extract_text("sample.pdf")`
- [ ] Implement annotation UI with OCR pre-fill
- [ ] Test annotation workflow with real documents
- [ ] Train GEPA pipeline with annotated examples
- [ ] Implement verification in production pipeline
- [ ] Set appropriate confidence thresholds
- [ ] Monitor match rates and confidence scores
- [ ] Adjust conflict strategy based on results

---

**Need Help?**
- Check full docs: [OCR_INTEGRATION_GUIDE.md](./services/OCR_INTEGRATION_GUIDE.md)
- Run tests: `python test_ocr_verification.py`
- Review code: `services/ocr/azure_service.py`, `services/models/verification.py`
