## GEPA Optimization Service

A reusable, schema-driven GEPA optimization service for document extraction pipelines.

### Overview

This service extracts the core GEPA optimization logic from `gepa_receipt_optimization.py` into a generalized, reusable module that works with **any document type** by accepting JSON schema definitions.

### Architecture

```
services/gepa/
├── optimizer.py          # Main orchestrator
├── schema_adapter.py     # JSON schema → DSPy signature
├── metric_factory.py     # Generic metrics with feedback
├── training_data.py      # Ground truth → DSPy examples
└── image_processor.py    # Image resizing/compression
```

### Key Features

- ✅ **Schema-Driven**: Define fields in JSON, get optimized extraction
- ✅ **Any Document Type**: Receipts, invoices, contracts, tax forms, etc.
- ✅ **GEPA-Compatible**: 5-parameter metrics with textual feedback
- ✅ **Rate-Limited**: Built-in delays to avoid API errors
- ✅ **Configurable**: LLM selection, image processing, GEPA parameters
- ✅ **Production-Ready**: Proper error handling, logging, and results

### Quick Start

#### 1. Define Your Schema

```python
from services.models import ExtractionSchema, FieldDefinition, FieldType

schema = ExtractionSchema(
    version=1,
    fields=[
        FieldDefinition(
            name="invoice_number",
            display_name="Invoice Number",
            description="Unique invoice identifier",
            data_type=FieldType.TEXT,
            required=True,
            extraction_hints=["Look for 'Invoice #' or 'Inv No.'"]
        ),
        FieldDefinition(
            name="total_amount",
            display_name="Total Amount",
            description="Final invoice total",
            data_type=FieldType.CURRENCY,
            required=True,
            extraction_hints=["Look for 'Total' at bottom of invoice"]
        )
    ]
)
```

#### 2. Prepare Ground Truth

```python
from services.models import GroundTruthExample

ground_truth = [
    GroundTruthExample(
        document_path='invoices/inv_001.pdf',
        labeled_values={
            'invoice_number': 'INV-123456',
            'total_amount': 1234.56
        }
    ),
    # ... more examples
]
```

#### 3. Configure Optimization

```python
from services.models import OptimizationConfig, LLMConfig

config = OptimizationConfig(
    student_llm=LLMConfig(
        provider="gemini",
        model_name="gemini-2.0-flash-exp",
        api_key=os.getenv("GEMINI_API_KEY")
    ),
    reflection_llm=LLMConfig(
        provider="gemini",
        model_name="gemini-2.0-flash-exp",
        api_key=os.getenv("GEMINI_API_KEY")
    ),
    delay_seconds=10.0,
    test_mode=False
)
```

#### 4. Run Optimization

```python
from services.gepa import GEPAOptimizer

optimizer = GEPAOptimizer(schema, config)
result = optimizer.optimize(ground_truth)

if result.success:
    print(f"Accuracy improved from {result.metrics.baseline_accuracy} "
          f"to {result.metrics.optimized_accuracy}")
    print(f"Optimized pipeline: {result.optimized_program_path}")
```

### Supported Field Types

- **TEXT**: String values (names, addresses, IDs)
- **NUMBER**: Numeric values (quantities, counts)
- **CURRENCY**: Monetary amounts (totals, prices)
- **DATE**: Date values (ISO format: YYYY-MM-DD)
- **EMAIL**: Email addresses
- **PHONE**: Phone numbers
- **ADDRESS**: Full addresses
- **BOOLEAN**: Yes/no values

### Configuration Options

#### LLM Configuration

```python
LLMConfig(
    provider="gemini",          # gemini, openai, anthropic, groq, openrouter
    model_name="model-name",    # Model identifier
    api_key="your-key",         # API key
    temperature=0,              # Sampling temperature
    max_tokens=None             # Optional token limit
)
```

#### GEPA Configuration

```python
GEPAConfig(
    auto="light",               # light/medium/heavy
    num_threads=1,              # 1 = sequential (avoids rate limits)
    reflection_minibatch_size=2,# Examples per reflection batch
    track_stats=True            # Track detailed statistics
)
```

#### Image Processing

```python
ImageProcessingConfig(
    max_width=512,              # Max width in pixels
    max_height=512,             # Max height in pixels
    jpeg_quality=60             # JPEG compression 1-100
)
```

### Examples

#### Example 1: Receipt Extraction

See `test_gepa_service.py` for a complete working example using the receipt schema.

#### Example 2: Invoice Extraction

```python
invoice_schema = ExtractionSchema(
    version=1,
    fields=[
        FieldDefinition(
            name="invoice_number",
            display_name="Invoice Number",
            description="Unique invoice identifier",
            data_type=FieldType.TEXT,
            required=True
        ),
        FieldDefinition(
            name="invoice_date",
            display_name="Invoice Date",
            description="Date invoice was issued",
            data_type=FieldType.DATE,
            required=True
        ),
        FieldDefinition(
            name="vendor_name",
            display_name="Vendor Name",
            description="Name of the vendor/supplier",
            data_type=FieldType.TEXT,
            required=True
        ),
        FieldDefinition(
            name="total_amount",
            display_name="Total Amount",
            description="Total invoice amount",
            data_type=FieldType.CURRENCY,
            required=True
        )
    ]
)

# Use exactly the same code as receipts!
optimizer = GEPAOptimizer(invoice_schema, config)
result = optimizer.optimize(invoice_ground_truth)
```

### How It Works

1. **Schema Adapter**: Converts your JSON schema to a DSPy `Signature` with proper Pydantic models
2. **Training Data Converter**: Loads images, resizes them, converts ground truth to DSPy format
3. **Metric Factory**: Creates a 5-parameter GEPA metric that compares predictions to ground truth and generates feedback
4. **Optimizer**: Orchestrates the entire GEPA optimization process:
   - Sets up LLMs (student + reflection)
   - Creates baseline DSPy program
   - Runs GEPA optimization with feedback
   - Tests and saves optimized program

### Best Practices

#### Rate Limiting

- Start with `delay_seconds=10` for Gemini free tier
- Use `num_threads=1` (sequential) to avoid bursts
- Enable `test_mode=True` for initial testing (uses only 4 examples)

#### Ground Truth Quality

- Provide at least 5-10 examples per document type
- More examples = better accuracy
- Diverse examples (different formats, layouts) help generalization

#### Schema Design

- Use clear, descriptive field names
- Provide detailed descriptions (LLM sees these!)
- Add extraction hints (e.g., "usually in top-right corner")
- Choose appropriate data types

#### Testing

```python
# Start with test mode
config = OptimizationConfig(..., test_mode=True, delay_seconds=5)

# Once working, switch to full mode
config = OptimizationConfig(..., test_mode=False, delay_seconds=10)
```

### Integration with OCR Mate Backend

This GEPA service will be used by the FastAPI backend:

```python
# In FastAPI route
@app.post("/document-types/{doc_type_id}/optimize")
async def optimize_pipeline(doc_type_id: str):
    # 1. Load document type and schema from database
    doc_type = await db.get_document_type(doc_type_id)
    schema = ExtractionSchema(**doc_type.schema)

    # 2. Load ground truth examples
    examples = await db.get_ground_truth_examples(doc_type_id)

    # 3. Run GEPA optimization
    optimizer = GEPAOptimizer(schema, config)
    result = optimizer.optimize(examples)

    # 4. Save result to database
    await db.save_pipeline(doc_type_id, result)

    return result
```

### Troubleshooting

#### "Rate limit exceeded"
- Increase `delay_seconds` (try 15 or 20)
- Ensure `num_threads=1`
- Reduce `reflection_minibatch_size` to 2 or 1

#### "Context length exceeded"
- Reduce `max_width` and `max_height` (try 256 or 384)
- Lower `jpeg_quality` (try 40 or 50)

#### "Failed to load image"
- Check that image paths are correct
- Ensure images are valid (not corrupted)
- Check file format (should be JPG, PNG, or PDF)

#### Low accuracy
- Add more ground truth examples
- Improve extraction hints in schema
- Try different LLM models
- Increase GEPA iterations (`auto="medium"` or `"heavy"`)

### Future Enhancements

- [ ] Multi-page document support
- [ ] Table extraction
- [ ] Confidence thresholds per field
- [ ] Active learning (suggest examples to label)
- [ ] Field dependencies (e.g., "total = subtotal + tax")
- [ ] Custom validation rules
- [ ] Async optimization for background jobs

### License

MIT License - Part of OCR Mate project
