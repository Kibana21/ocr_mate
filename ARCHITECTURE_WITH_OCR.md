# OCR Mate Architecture - Complete Flow

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           OCR MATE PLATFORM                                 │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND (HTML/CSS/JS)                           │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Document     │  │ Schema       │  │ Annotation   │             │   │
│  │  │ Type Manager │  │ Editor       │  │ UI           │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │         │                 │                  │                      │   │
│  └─────────┼─────────────────┼──────────────────┼──────────────────────┘   │
│            │                 │                  │                           │
│            │                 │                  │                           │
│            └─────────────────┴──────────────────┘                           │
│                              │                                               │
│                              │ HTTP REST API                                │
│                              ↓                                               │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    BACKEND API (FastAPI)                            │   │
│  │                                                                      │   │
│  │  POST /api/annotations/create         ← Upload document             │   │
│  │  PUT  /api/annotations/{id}/fields    ← Edit field value            │   │
│  │  POST /api/annotations/{id}/verify    ← Verify field                │   │
│  │  POST /api/optimize                   ← Start GEPA optimization     │   │
│  │  POST /api/extractions/process        ← Process new document        │   │
│  │                                                                      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              │                                               │
│                              ↓                                               │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    SERVICE LAYER                                    │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  OCR Service (services/ocr/)                                 │  │   │
│  │  │  ├─ AzureDocumentIntelligenceService                         │  │   │
│  │  │  └─ Extracts text, layout, bounding boxes                    │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  Annotation Service (services/models/annotation.py)          │  │   │
│  │  │  ├─ OCRAssistedAnnotationService                             │  │   │
│  │  │  ├─ Creates pre-filled annotations from OCR                  │  │   │
│  │  │  └─ Tracks field sources (OCR auto, user edited, manual)     │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  GEPA Optimizer (services/gepa/)                             │  │   │
│  │  │  ├─ GEPAOptimizer (orchestrator)                             │  │   │
│  │  │  ├─ SchemaAdapter (schema → DSPy signature)                  │  │   │
│  │  │  ├─ MetricFactory (creates GEPA metrics)                     │  │   │
│  │  │  ├─ TrainingDataConverter (converts ground truth)            │  │   │
│  │  │  └─ ImageProcessor (loads & resizes images)                  │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  Verification Service (services/models/verification.py)      │  │   │
│  │  │  ├─ DualExtractionVerifier                                   │  │   │
│  │  │  ├─ Runs OCR + LLM extraction in parallel                    │  │   │
│  │  │  ├─ Compares results field-by-field                          │  │   │
│  │  │  └─ Generates confidence scores & flags conflicts            │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              │                                               │
│                              ↓                                               │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    EXTERNAL SERVICES                                │   │
│  │                                                                      │   │
│  │  ┌──────────────────────┐  ┌──────────────────────┐               │   │
│  │  │ Azure Document       │  │ LLM APIs             │               │   │
│  │  │ Intelligence         │  │ - Gemini             │               │   │
│  │  │ (OCR)                │  │ - OpenAI GPT-4       │               │   │
│  │  │                      │  │ - Claude 3.5         │               │   │
│  │  └──────────────────────┘  └──────────────────────┘               │   │
│  │                                                                      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow 1: Creating Ground Truth with OCR Assistance

```
┌─────────────────────────────────────────────────────────────────────────┐
│  USER: Create Ground Truth Example                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 1: User defines schema                 │
          │  - merchant_name (TEXT)                      │
          │  - transaction_date (DATE)                   │
          │  - total (CURRENCY)                          │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 2: User uploads document               │
          │  📄 receipt_123.jpg                          │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 3: System runs OCR                     │
          │  AzureDocumentIntelligenceService            │
          │    .extract_text(receipt_123.jpg)            │
          │                                              │
          │  Returns:                                    │
          │  ┌────────────────────────────────────────┐ │
          │  │ OCRResult                              │ │
          │  │  pages: [OCRPage]                      │ │
          │  │  full_text: "Store ABC\n               │ │
          │  │              Date: 01/15/2024\n        │ │
          │  │              Total: $25.99"            │ │
          │  │  lines: [OCRLine with bounding boxes] │ │
          │  └────────────────────────────────────────┘ │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 4: System matches OCR to schema        │
          │  OCRAssistedAnnotationService                │
          │    .create_annotation(doc, schema)           │
          │                                              │
          │  Uses keyword matching:                      │
          │  - "merchant_name" → finds "Store ABC"       │
          │  - "date" → finds "01/15/2024"               │
          │  - "total" → finds "$25.99"                  │
          │                                              │
          │  Returns:                                    │
          │  ┌────────────────────────────────────────┐ │
          │  │ DocumentAnnotation                     │ │
          │  │  annotations: [                        │ │
          │  │    FieldAnnotation(                    │ │
          │  │      field_name="merchant_name"        │ │
          │  │      value="Store ABC"                 │ │
          │  │      source=OCR_AUTO                   │ │
          │  │      ocr_confidence=0.75               │ │
          │  │      user_verified=False               │ │
          │  │    ),                                  │ │
          │  │    FieldAnnotation(...)                │ │
          │  │  ]                                     │ │
          │  └────────────────────────────────────────┘ │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 5: UI displays pre-filled form         │
          │  ┌────────────────────────────────────────┐ │
          │  │ Merchant Name: Store ABC         ✓ │⚠️│ │
          │  │ Date:          01/15/2024        ✓ │  │ │
          │  │ Total:         $25.99            ✓ │⚠️│ │
          │  │                                      │ │ │
          │  │ ✓ = Verify button                    │ │
          │  │ ⚠️ = Low confidence indicator         │ │
          │  └────────────────────────────────────────┘ │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 6: User reviews and corrects           │
          │                                              │
          │  User actions:                               │
          │  ✅ Clicks ✓ on "merchant_name" (verified)   │
          │  ✅ Clicks ✓ on "date" (verified)            │
          │  ✏️ Edits "total" from $25.99 → $26.49       │
          │                                              │
          │  Backend updates:                            │
          │  annotation.mark_field_verified("merchant")  │
          │  annotation.mark_field_verified("date")      │
          │  annotation.set_field_value(                 │
          │    "total", 26.49, USER_EDITED               │
          │  )                                           │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 7: Check completion                    │
          │  annotation.get_completion_status(schema)    │
          │                                              │
          │  Returns:                                    │
          │  {                                           │
          │    "annotated_fields": 3,                    │
          │    "verified_fields": 3,                     │
          │    "is_complete": True ✓                     │
          │  }                                           │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 8: Save as ground truth                │
          │                                              │
          │  ground_truth = GroundTruthExample(          │
          │    document_path="receipt_123.jpg",          │
          │    labeled_values={                          │
          │      "merchant_name": "Store ABC",           │
          │      "transaction_date": "01/15/2024",       │
          │      "total": 26.49  ← User corrected        │
          │    }                                         │
          │  )                                           │
          │                                              │
          │  database.save(ground_truth)                 │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  ✅ Ground truth created!                     │
          │                                              │
          │  Time saved: ~5 minutes (only 1 correction)  │
          │  vs. typing all 3 fields manually            │
          └──────────────────────────────────────────────┘
```

---

## Workflow 2: GEPA Optimization (Unchanged)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  USER: Optimize Pipeline with 5 Ground Truth Examples                   │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 1: User clicks "Optimize"              │
          │                                              │
          │  Input:                                      │
          │  - schema (ReceiptSchema)                    │
          │  - ground_truth_examples (5 annotated docs)  │
          │  - config (LLM settings, GEPA params)        │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 2: GEPAOptimizer.optimize()            │
          │                                              │
          │  2.1: SchemaAdapter converts schema          │
          │       → Creates dynamic Pydantic model       │
          │       → Creates DSPy Signature               │
          │                                              │
          │  2.2: MetricFactory creates metric           │
          │       → 5-parameter GEPA metric              │
          │       → Field-specific feedback              │
          │                                              │
          │  2.3: TrainingDataConverter converts data    │
          │       → Loads images                         │
          │       → Creates dspy.Example objects         │
          │       → 80/20 train/val split                │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 3: GEPA optimization runs              │
          │                                              │
          │  3.1: Create baseline program                │
          │       baseline = dspy.Predict(Signature)     │
          │                                              │
          │  3.2: Run GEPA                               │
          │       optimizer = dspy.GEPA(                 │
          │         metric=metric_fn,                    │
          │         num_threads=1,                       │
          │         reflection_lm=reflection_llm         │
          │       )                                      │
          │       optimized = optimizer.compile(         │
          │         student=baseline,                    │
          │         trainset=train_examples              │
          │       )                                      │
          │                                              │
          │  3.3: GEPA iterates:                         │
          │       → Student LLM extracts fields          │
          │       → Metric compares to ground truth      │
          │       → Reflection LLM generates feedback    │
          │       → Prompts improved with feedback       │
          │       → Repeat until optimal                 │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 4: Save optimized pipeline             │
          │                                              │
          │  optimized.save(                             │
          │    "pipelines/receipt_optimized.json"        │
          │  )                                           │
          │                                              │
          │  Returns:                                    │
          │  OptimizationResult(                         │
          │    success=True,                             │
          │    metrics={                                 │
          │      baseline_accuracy: 0.60,                │
          │      optimized_accuracy: 0.92,               │
          │      improvement: 53%                        │
          │    }                                         │
          │  )                                           │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  ✅ Pipeline optimized and ready!             │
          │                                              │
          │  Pipeline saved to:                          │
          │  pipelines/receipt_optimized.json            │
          └──────────────────────────────────────────────┘
```

---

## Workflow 3: Production Extraction with Dual Verification

```
┌─────────────────────────────────────────────────────────────────────────┐
│  USER: Process New Document with Verification                           │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 1: User uploads new document           │
          │  📄 new_receipt.jpg                          │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 2: Load optimized pipeline             │
          │  llm_extractor = dspy.Predict.load(          │
          │    "pipelines/receipt_optimized.json"        │
          │  )                                           │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 3: Create verifier                     │
          │  verifier = DualExtractionVerifier(          │
          │    ocr_service=ocr_service,                  │
          │    llm_extractor=llm_extractor,              │
          │    conflict_strategy=HIGHER_CONFIDENCE       │
          │  )                                           │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 4: Run dual extraction (PARALLEL)      │
          │                                              │
          │  ┌────────────────────┐  ┌────────────────┐ │
          │  │ OCR Extraction     │  │ LLM Extraction │ │
          │  │ (Fast, Cheap)      │  │ (Smart, Slow)  │ │
          │  │                    │  │                │ │
          │  │ Azure Doc Intel    │  │ Optimized      │ │
          │  │  .extract_text()   │  │ Pipeline       │ │
          │  │                    │  │  (image)       │ │
          │  │ Returns:           │  │                │ │
          │  │ {                  │  │ Returns:       │ │
          │  │   merchant: "ABC"  │  │ {              │ │
          │  │   date: "01/15"    │  │   merchant:    │ │
          │  │   total: "$26.50"  │  │     "ABC"      │ │
          │  │ }                  │  │   date:        │ │
          │  │ confidence: 0.7    │  │     "01/15"    │ │
          │  │                    │  │   total:       │ │
          │  │                    │  │     "$26.49"   │ │
          │  │                    │  │ }              │ │
          │  │                    │  │ confidence:0.9 │ │
          │  └────────────────────┘  └────────────────┘ │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 5: Compare results field-by-field      │
          │                                              │
          │  For each field:                             │
          │  ┌────────────────────────────────────────┐ │
          │  │ Field: merchant_name                   │ │
          │  │   OCR: "ABC" (conf: 0.7)               │ │
          │  │   LLM: "ABC" (conf: 0.9)               │ │
          │  │   Match? YES ✓                         │ │
          │  │   Final: "ABC"                         │ │
          │  │   Confidence: 0.85 (boosted by match)  │ │
          │  └────────────────────────────────────────┘ │
          │                                              │
          │  ┌────────────────────────────────────────┐ │
          │  │ Field: total                           │ │
          │  │   OCR: "$26.50" (conf: 0.7)            │ │
          │  │   LLM: "$26.49" (conf: 0.9)            │ │
          │  │   Match? NO (within 1% tolerance) ✓    │ │
          │  │   Status: MATCH (normalized)           │ │
          │  │   Final: "$26.49" (prefer LLM)         │ │
          │  │   Confidence: 0.85                     │ │
          │  └────────────────────────────────────────┘ │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 6: Calculate metrics                   │
          │                                              │
          │  overall_confidence = avg(field_confidences) │
          │                     = 0.85                   │
          │                                              │
          │  match_rate = matches / total_fields         │
          │             = 3 / 3 = 100%                   │
          │                                              │
          │  needs_review = confidence < 0.6             │
          │               = False                        │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 7: Route based on confidence           │
          │                                              │
          │  if confidence >= 0.9:                       │
          │    ✅ AUTO-APPROVE                            │
          │    Save extraction with status="approved"    │
          │                                              │
          │  elif confidence >= 0.6:                     │
          │    ⚠️ AUTO-SAVE, FLAG FOR SPOT CHECK         │
          │    Save extraction with status="review"      │
          │                                              │
          │  else:                                       │
          │    ❌ HUMAN REVIEW REQUIRED                   │
          │    Add to review queue with conflicts        │
          │                                              │
          │  In this case: 0.85 ≥ 0.6 → Auto-save       │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  Step 8: Return result to user               │
          │                                              │
          │  {                                           │
          │    "extraction": {                           │
          │      "merchant_name": "ABC",                 │
          │      "date": "01/15/2024",                   │
          │      "total": 26.49                          │
          │    },                                        │
          │    "confidence": 0.85,                       │
          │    "match_rate": 1.0,                        │
          │    "status": "approved",                     │
          │    "needs_review": false                     │
          │  }                                           │
          └──────────────────────────────────────────────┘
                                 │
                                 ↓
          ┌──────────────────────────────────────────────┐
          │  ✅ Extraction complete with confidence!      │
          │                                              │
          │  Benefits:                                   │
          │  - Know extraction is trustworthy (85% conf) │
          │  - OCR + LLM agree (100% match rate)         │
          │  - Auto-approved (no manual review needed)   │
          └──────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA MODELS & FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

1. Schema Definition (User Input)
   ↓
   ExtractionSchema {
     version: 1,
     fields: [
       FieldDefinition {
         name: "merchant_name",
         data_type: FieldType.TEXT,
         required: true,
         extraction_hints: ["Store name", "Merchant"]
       },
       ...
     ]
   }

2. Ground Truth Annotation (OCR-Assisted)
   ↓
   DocumentAnnotation {
     document_path: "receipt_1.jpg",
     annotations: [
       FieldAnnotation {
         field_name: "merchant_name",
         value: "Store ABC",
         source: AnnotationSource.OCR_AUTO,
         ocr_confidence: 0.75,
         user_verified: false
       },
       ...
     ]
   }
   ↓
   (User reviews and verifies)
   ↓
   GroundTruthExample {
     document_path: "receipt_1.jpg",
     labeled_values: {
       "merchant_name": "Store ABC",
       "total": 26.49
     }
   }

3. GEPA Optimization
   ↓
   OptimizationConfig {
     student_llm: LLMConfig,
     reflection_llm: LLMConfig,
     gepa: GEPAConfig
   }
   ↓
   GEPAOptimizer.optimize(ground_truth_examples)
   ↓
   OptimizationResult {
     success: true,
     metrics: OptimizationMetrics {
       baseline_accuracy: 0.60,
       optimized_accuracy: 0.92
     },
     artifacts: {
       "saved_path": "pipelines/optimized.json"
     }
   }

4. Production Extraction with Verification
   ↓
   DualExtractionVerifier.verify_extraction(new_document)
   ↓
   DocumentVerification {
     field_verifications: [
       FieldVerification {
         field_name: "merchant_name",
         ocr_value: "ABC",
         llm_value: "ABC",
         final_value: "ABC",
         status: VerificationStatus.MATCH,
         confidence_score: 0.85
       },
       ...
     ],
     overall_confidence: 0.85,
     match_rate: 1.0,
     needs_human_review: false
   }
   ↓
   Final Extraction {
     "merchant_name": "ABC",
     "total": 26.49,
     "_metadata": {
       "confidence": 0.85,
       "status": "approved"
     }
   }
```

---

## File Organization

```
ocr_mate/
├── services/
│   ├── __init__.py
│   │
│   ├── models/                          # Data models
│   │   ├── __init__.py
│   │   ├── schema.py                    # ExtractionSchema, FieldDefinition
│   │   ├── annotation.py                # NEW: OCR-assisted annotation
│   │   ├── verification.py              # NEW: Dual extraction verification
│   │   ├── optimization_config.py       # LLMConfig, GEPAConfig
│   │   └── optimization_result.py       # OptimizationResult, metrics
│   │
│   ├── ocr/                             # NEW: OCR services
│   │   ├── __init__.py
│   │   └── azure_service.py             # Azure Document Intelligence client
│   │
│   ├── gepa/                            # GEPA optimization
│   │   ├── __init__.py
│   │   ├── optimizer.py                 # Main GEPAOptimizer
│   │   ├── schema_adapter.py            # Schema → DSPy Signature
│   │   ├── metric_factory.py            # Create GEPA metrics
│   │   ├── training_data.py             # Convert ground truth
│   │   ├── image_processor.py           # Load & resize images
│   │   └── README.md
│   │
│   ├── OCR_INTEGRATION_GUIDE.md         # NEW: Comprehensive OCR guide
│   └── OCR_ENHANCEMENT_SUMMARY.md       # NEW: Quick summary
│
├── test_gepa_service.py                 # Original GEPA test
├── test_ocr_verification.py             # NEW: OCR workflow tests
├── gepa_receipt_optimization.py         # Original receipt script
└── REQUIREMENTS.md                      # Product requirements
```

---

## Key Architectural Decisions

### 1. OCR Integration is Optional

```python
# Without OCR (still works)
optimizer = GEPAOptimizer(schema, config)
result = optimizer.optimize(ground_truth_examples)

# With OCR annotation (faster ground truth creation)
annotation_service = OCRAssistedAnnotationService(ocr_service)
annotation = annotation_service.create_annotation(doc, schema)
ground_truth = annotation.to_ground_truth()

# With OCR verification (confidence scoring)
verifier = DualExtractionVerifier(ocr_service, llm_extractor)
verification = verifier.verify_extraction(doc, schema)
```

### 2. Two Separate OCR Use Cases

**Use Case 1: Annotation** (Always beneficial)
- Pre-fills forms → Saves time
- No accuracy impact on training
- Recommended: Always enable

**Use Case 2: Verification** (Conditional benefit)
- Adds confidence scoring → Better quality control
- Adds OCR cost per document
- Recommended: Enable for high-volume or high-stakes

### 3. Separation of Concerns

```
┌────────────────────────────────────────┐
│  OCR Service                           │  ← Extracts text from images
│  (services/ocr/)                       │     (Azure Document Intelligence)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Annotation Service                    │  ← Creates OCR-assisted annotations
│  (services/models/annotation.py)       │     (Uses OCR service)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  GEPA Optimizer                        │  ← Trains extraction pipeline
│  (services/gepa/)                      │     (Uses ground truth from annotations)
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Verification Service                  │  ← Verifies production extractions
│  (services/models/verification.py)     │     (Uses OCR + trained pipeline)
└────────────────────────────────────────┘
```

### 4. Schema-Driven Design Throughout

Everything derives from the `ExtractionSchema`:
- OCR annotation knows which fields to look for
- GEPA optimizer creates dynamic signatures
- Verifier knows how to compare field values (type-aware)

---

## Summary

This architecture provides:

✅ **Modular Design**: Each service is independent
✅ **Optional Enhancements**: OCR can be enabled/disabled
✅ **No Breaking Changes**: Existing code still works
✅ **Clear Data Flow**: Schema → Annotation → Training → Verification
✅ **Type Safety**: Pydantic models throughout
✅ **Comprehensive Testing**: Test scripts for each workflow

Ready to build the UI! 🚀
