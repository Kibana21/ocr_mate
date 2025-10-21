# Schema to Signature Conversion - Explained

**How OCR Mate converts your JSON schema to DSPy Signatures**

---

## Overview

The conversion happens in 2 steps:
1. **Schema → Pydantic Model** (defines the output structure)
2. **Schema + Model → DSPy Signature** (defines the LLM task)

Let's walk through a real example!

---

## Step-by-Step Example

### Input: Your Schema Definition

```python
from services.models import ExtractionSchema, FieldDefinition, FieldType

schema = ExtractionSchema(
    version=1,
    fields=[
        FieldDefinition(
            name="merchant_name",
            display_name="Merchant Name",
            description="Name of the store or merchant",
            data_type=FieldType.TEXT,
            required=True,
            extraction_hints=["Store name at top", "Business name"]
        ),
        FieldDefinition(
            name="total",
            display_name="Total Amount",
            description="Final total amount to pay",
            data_type=FieldType.CURRENCY,
            required=True,
            extraction_hints=["Total", "Grand Total", "Amount due"]
        ),
        FieldDefinition(
            name="date",
            display_name="Date",
            description="Transaction date",
            data_type=FieldType.DATE,
            required=True,
            extraction_hints=["Date", "Transaction date"]
        ),
    ]
)
```

---

## STEP 1: Schema → Pydantic Model

**Code**: `create_pydantic_model_from_schema(schema)` in [schema_adapter.py:30-94](schema_adapter.py#L30-L94)

### What Happens:

```python
# For each field in schema:
field_definitions = {}

for field_def in schema.fields:
    # 1. Map FieldType to Python type
    python_type = field_type_to_python_type(field_def.data_type)
    # FieldType.TEXT     → str
    # FieldType.CURRENCY → float
    # FieldType.DATE     → str

    # 2. Make optional if not required
    if not field_def.required:
        python_type = Optional[python_type]

    # 3. Create Pydantic Field with metadata
    pydantic_field = Field(
        default=None if not field_def.required else ...,
        description=field_def.description
    )

    # 4. Add to field definitions
    field_definitions[field_def.name] = (python_type, pydantic_field)
```

### Result: Dynamic Pydantic Model

```python
# Dynamically created class (equivalent to):
class DynamicExtractionModel(BaseModel):
    merchant_name: str = Field(
        ...,
        description="Name of the store or merchant"
    )
    total: float = Field(
        ...,
        description="Final total amount to pay"
    )
    date: str = Field(
        ...,
        description="Transaction date"
    )
```

**This model defines the OUTPUT structure** that the LLM must return.

---

## STEP 2: Schema + Model → DSPy Signature

**Code**: `create_dspy_signature_from_schema(schema, model, use_ocr_grounding)` in [schema_adapter.py:97-157](schema_adapter.py#L97-L157)

### What Happens:

#### A) Build Instruction Text

```python
# 1. Get schema description
schema_description = schema.to_prompt_description()
# Returns:
"""
Extract the following fields from the document:
- Merchant Name (text) (required): Name of the store or merchant
  • Store name at top
  • Business name
- Total Amount (currency) (required): Final total amount to pay
  • Total
  • Grand Total
  • Amount due
- Date (date) (required): Transaction date
  • Date
  • Transaction date
"""

# 2. Build full instruction
if use_ocr_grounding:
    instruction = f"""Extract structured data from the document using BOTH the image and OCR text.

The OCR text provides the textual content for reference. Use the image for visual context and verification.

{schema_description}

Return values in a structured format. Cross-reference between OCR text and image for accuracy."""
else:
    instruction = f"""Extract structured data from the document image.

{schema_description}

Return values in a structured format. Be precise and extract exact values from the document."""
```

#### B) Create DSPy Signature Class

**Without OCR Grounding** (vision-only):
```python
class DynamicExtraction(dspy.Signature):
    __doc__ = instruction  # The instruction we built above

    # INPUT FIELD
    document_image: dspy.Image = dspy.InputField(
        desc="Document image to extract data from"
    )

    # OUTPUT FIELD (uses the Pydantic model we created!)
    extracted_data: DynamicExtractionModel = dspy.OutputField(
        desc="Extracted structured data"
    )
```

**With OCR Grounding** (dual-input):
```python
class DynamicExtractionWithOCR(dspy.Signature):
    __doc__ = instruction  # Enhanced instruction mentioning both inputs

    # INPUT FIELD 1: Image
    document_image: dspy.Image = dspy.InputField(
        desc="Document image for visual context"
    )

    # INPUT FIELD 2: OCR Text ← NEW!
    ocr_text: str = dspy.InputField(
        desc="OCR-extracted text from the document for textual reference"
    )

    # OUTPUT FIELD (same Pydantic model)
    extracted_data: DynamicExtractionModel = dspy.OutputField(
        desc="Extracted structured data"
    )
```

---

## Visual Flow

```
┌─────────────────────────────────────┐
│  ExtractionSchema (Your Input)      │
│  ┌─────────────────────────────┐   │
│  │ fields:                      │   │
│  │  - merchant_name (TEXT)      │   │
│  │  - total (CURRENCY)          │   │
│  │  - date (DATE)               │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
               │ Step 1: create_pydantic_model_from_schema()
               ▼
┌─────────────────────────────────────┐
│  Pydantic Model (Output Structure)  │
│  ┌─────────────────────────────┐   │
│  │ class DynamicExtractionModel│   │
│  │   merchant_name: str        │   │
│  │   total: float              │   │
│  │   date: str                 │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
               │ Step 2: create_dspy_signature_from_schema()
               ▼
┌─────────────────────────────────────┐
│  DSPy Signature (LLM Task)          │
│  ┌─────────────────────────────┐   │
│  │ INPUT:                       │   │
│  │   document_image: Image      │   │
│  │   ocr_text: str  ← OCR!      │   │
│  │                              │   │
│  │ OUTPUT:                      │   │
│  │   extracted_data:            │   │
│  │     DynamicExtractionModel   │   │
│  │                              │   │
│  │ INSTRUCTION:                 │   │
│  │   "Extract using BOTH..."    │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
               │ Used in: dspy.Predict(signature)
               ▼
         ┌─────────────┐
         │ LLM Program │
         └─────────────┘
```

---

## Real Output Example

Let's see what the actual generated signature looks like:

### The Generated Instruction:
```
Extract structured data from the document using BOTH the image and OCR text.

The OCR text provides the textual content for reference. Use the image for visual context and verification.

Extract the following fields from the document:
- Merchant Name (text) (required): Name of the store or merchant
  • Store name at top
  • Business name
- Total Amount (currency) (required): Final total amount to pay
  • Total
  • Grand Total
  • Amount due
- Date (date) (required): Transaction date
  • Date
  • Transaction date

Return values in a structured format. Cross-reference between OCR text and image for accuracy.
```

### The Generated Signature:
```python
class DynamicExtractionWithOCR(dspy.Signature):
    """<instruction above>"""

    document_image: dspy.Image = dspy.InputField(
        desc="Document image for visual context"
    )

    ocr_text: str = dspy.InputField(
        desc="OCR-extracted text from the document for textual reference"
    )

    extracted_data: DynamicExtractionModel = dspy.OutputField(
        desc="Extracted structured data"
    )
```

Where `DynamicExtractionModel` is:
```python
class DynamicExtractionModel(BaseModel):
    merchant_name: str = Field(..., description="Name of the store or merchant")
    total: float = Field(..., description="Final total amount to pay")
    date: str = Field(..., description="Transaction date")
```

---

## How It's Used

### 1. Creating the Program

```python
from services.gepa.schema_adapter import SchemaAdapter

# Create adapter with OCR grounding enabled
adapter = SchemaAdapter(schema, use_ocr_grounding=True)

# Get the signature
signature = adapter.get_dspy_signature()

# Create DSPy program
program = dspy.Predict(signature)
```

### 2. Running Extraction

```python
# With OCR grounding (dual input)
result = program(
    document_image=image,      # Visual input
    ocr_text=ocr_markdown      # Textual input
)

# Access extracted data
print(result.extracted_data.merchant_name)  # "COMFORT TRANSPORTATION"
print(result.extracted_data.total)           # 25.3
print(result.extracted_data.date)            # "16/11/2019"
```

---

## Key Functions Breakdown

### 1. `field_type_to_python_type()` - Line 15

Maps your `FieldType` enum to Python types:

```python
FieldType.TEXT      → str
FieldType.NUMBER    → float
FieldType.CURRENCY  → float
FieldType.DATE      → str
FieldType.EMAIL     → str
FieldType.PHONE     → str
FieldType.ADDRESS   → str
FieldType.BOOLEAN   → bool
```

### 2. `create_pydantic_model_from_schema()` - Line 30

Creates a dynamic Pydantic model class from your schema fields.

**Input**: `ExtractionSchema` with 3 fields
**Output**: `DynamicExtractionModel` class with 3 Pydantic fields

**Key technique**: Uses `pydantic.create_model()` to dynamically create a class at runtime.

### 3. `create_dspy_signature_from_schema()` - Line 97

Creates a DSPy Signature from your schema.

**Input**:
- `ExtractionSchema` (your fields)
- `extraction_model` (Pydantic model from step 2)
- `use_ocr_grounding` (True/False)

**Output**: `DynamicExtraction` or `DynamicExtractionWithOCR` class

**Key decision**:
- If `use_ocr_grounding=False`: Single input (document_image)
- If `use_ocr_grounding=True`: Dual input (document_image + ocr_text)

### 4. `SchemaAdapter` Class - Line 159

Convenience wrapper that manages the conversion process.

```python
# Vision-only
adapter = SchemaAdapter(schema, use_ocr_grounding=False)

# OCR-grounded
adapter = SchemaAdapter(schema, use_ocr_grounding=True)

# Get components
model = adapter.get_extraction_model()      # Pydantic model
signature = adapter.get_dspy_signature()    # DSPy signature
program = adapter.create_dspy_program()     # dspy.Predict
```

---

## Special Features

### XML Value Extraction (Lines 70-93)

The generated Pydantic model includes a validator that handles LLM responses wrapped in XML:

```python
@field_validator('*', mode='before')
@classmethod
def extract_from_xml(cls, v):
    """Extract value from XML tags if present"""
    if isinstance(v, str):
        # LLM might return: <total>25.30</total>
        # Validator extracts: 25.30
        match = re.search(r'<[^>]+>([^<]+)</[^>]+>', v)
        if match:
            v = match.group(1).strip()

        # Also handles currency symbols: $25.30 → 25.30
        v_clean = v.replace('$', '').replace(',', '').strip()
        try:
            return float(v_clean)
        except ValueError:
            return v
    return v
```

This makes the extraction robust to different LLM output formats.

---

## Testing the Conversion

Want to see it in action? Run this:

```python
from services.models import ExtractionSchema, FieldDefinition, FieldType
from services.gepa.schema_adapter import SchemaAdapter

# Define schema
schema = ExtractionSchema(
    version=1,
    fields=[
        FieldDefinition(
            name="merchant_name",
            display_name="Merchant Name",
            description="Name of the store",
            data_type=FieldType.TEXT,
            required=True
        ),
        FieldDefinition(
            name="total",
            display_name="Total",
            description="Total amount",
            data_type=FieldType.CURRENCY,
            required=True
        ),
    ]
)

# Create adapter (with OCR grounding!)
adapter = SchemaAdapter(schema, use_ocr_grounding=True)

# Get components
model = adapter.get_extraction_model()
signature = adapter.get_dspy_signature()

# Inspect
print("="*80)
print("PYDANTIC MODEL")
print("="*80)
print(f"Class name: {model.__name__}")
print(f"Fields: {list(model.model_fields.keys())}")

print("\n" + "="*80)
print("DSPY SIGNATURE")
print("="*80)
print(f"Class name: {signature.__name__}")
print(f"\nInstruction:\n{signature.__doc__}")
print(f"\nInput fields:")
for field in signature.fields:
    if not field.prefix.startswith("Extracted"):
        print(f"  - {field.prefix}")
print(f"\nOutput field:")
for field in signature.fields:
    if field.prefix.startswith("Extracted"):
        print(f"  - {field.prefix}")
```

**Output**:
```
================================================================================
PYDANTIC MODEL
================================================================================
Class name: DynamicExtractionModel
Fields: ['merchant_name', 'total']

================================================================================
DSPY SIGNATURE
================================================================================
Class name: DynamicExtractionWithOCR

Instruction:
Extract structured data from the document using BOTH the image and OCR text.

The OCR text provides the textual content for reference. Use the image for visual context and verification.

Extract the following fields from the document:
- Merchant Name (text) (required): Name of the store
- Total (currency) (required): Total amount

Return values in a structured format. Cross-reference between OCR text and image for accuracy.

Input fields:
  - Document Image:
  - Ocr Text:

Output field:
  - Extracted Data:
```

---

## Why This Design?

### 1. **Flexibility**: Change schema without changing code
You define fields in JSON/Python, not hardcoded signatures.

### 2. **Type Safety**: Pydantic validates LLM outputs
The generated model ensures LLM returns correct types.

### 3. **Modularity**: Same schema works for different extraction modes
- Vision-only: `use_ocr_grounding=False`
- OCR-grounded: `use_ocr_grounding=True`

### 4. **Clarity**: Schema captures domain knowledge
Your extraction hints guide the LLM without prompt engineering.

---

## Summary

```
Your Schema Definition
        ↓
    [Step 1]
        ↓
Pydantic Model (output structure)
        ↓
    [Step 2]
        ↓
DSPy Signature (LLM task)
        ↓
dspy.Predict(signature)
        ↓
Trained Pipeline
```

**Key Files**:
- [schema_adapter.py](services/gepa/schema_adapter.py) - All conversion logic
- [schema.py](services/models/schema.py) - Schema definitions

**Key Insight**:
The schema is **NOT a prompt** - it's a **structured definition** that gets converted to:
1. A Pydantic model (for validation)
2. A DSPy signature (for the LLM task)

The actual prompt/instruction is **generated automatically** from the schema!

---

**Now you understand how schema → signature conversion works!** 🎓

Any questions about specific parts of the conversion?
