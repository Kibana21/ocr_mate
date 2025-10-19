# OCR Mate: Intelligent Structured Document Extraction Platform

## Product Requirements Document (PRD)
**Version:** 1.0
**Date:** October 2025
**Status:** Draft

---

## Executive Summary

OCR Mate is an intelligent web-based platform that enables users to create custom document extraction pipelines without writing code. By combining OCR technology, DSPy's GEPA optimizer, and few-shot learning, users can define document types, specify extraction fields, provide ground truth examples, and automatically generate optimized extraction pipelines that improve over time.

### Inspiration: Learning from LangStruct

OCR Mate builds on the excellent foundation laid by [LangStruct](https://langstruct.dev/), adopting their best practices while extending structured extraction to physical document processing:

**What we adopt from LangStruct:**
- **Zero prompt engineering required** - Users provide examples, system auto-optimizes
- **Multi-model flexibility** - Switch between OpenAI, Claude, Gemini, local models in one click
- **Source attribution and traceability** - Show exactly where each extracted value came from
- **Automatic DSPy-based optimization** - Programming, not prompting
- **Developer-friendly API** - Clean REST API with comprehensive documentation

**How we extend beyond LangStruct:**
- **Full document pipeline** - OCR → Extraction → Validation (not just text extraction)
- **Visual annotation interface** - Purpose-built for non-technical business users
- **GEPA optimizer** - State-of-the-art textual feedback + Pareto frontier optimization
- **Batch document processing** - Handle thousands of documents at scale
- **Business-focused workflows** - Review queues, team collaboration, audit trails
- **Enterprise features** - SSO, on-premise deployment, compliance tools

**Market Position**: "LangStruct for documents, built for business users, powered by GEPA."

---

## 1. Vision & Goals

### 1.1 Vision Statement
Democratize structured document extraction by enabling non-technical users to build production-ready OCR extraction pipelines through an intuitive web interface, powered by state-of-the-art LLM optimization.

### 1.2 Core Objectives
- **Ease of Use**: Zero-code interface for defining extraction schemas
- **Accuracy**: Leverage GEPA optimization to achieve 90%+ extraction accuracy
- **Flexibility**: Support arbitrary document types and field structures
- **Scalability**: Handle high-volume document processing
- **Continuous Improvement**: Learn from user corrections to improve extraction quality

### 1.3 Success Metrics
- Time to create extraction pipeline: < 15 minutes
- Extraction accuracy after optimization: > 90%
- User satisfaction score: > 4.5/5
- Processing throughput: > 100 documents/minute
- Pipeline improvement rate: +5-10% accuracy per 100 labeled examples

---

## 2. User Personas

### 2.1 Primary Persona: Business Analyst (Sarah)
- **Role**: Operations analyst at mid-sized company
- **Pain Points**:
  - Manual data entry from invoices/receipts
  - Generic OCR tools don't understand her specific document formats
  - Vendor solutions require long implementation cycles
- **Goals**:
  - Extract structured data from 500+ invoices daily
  - Customize fields to match internal systems
  - Reduce manual validation time by 80%

### 2.2 Secondary Persona: Data Engineer (Raj)
- **Role**: ML engineer building document automation
- **Pain Points**:
  - Writing custom extraction code for each document type
  - Maintaining brittle regex/rule-based parsers
  - Long iteration cycles for prompt engineering
- **Goals**:
  - Rapidly prototype extraction pipelines
  - Export optimized prompts/code for production
  - Integrate with existing data pipelines via API

### 2.3 Tertiary Persona: Compliance Officer (Maria)
- **Role**: Regulatory compliance at financial institution
- **Pain Points**:
  - Extracting specific fields from regulatory documents
  - Ensuring audit trail for extracted data
  - Validating extraction accuracy
- **Goals**:
  - Define extraction schemas matching regulatory requirements
  - Track extraction confidence scores
  - Export audit logs for compliance

---

## 3. Core Features & Functionality

### 3.1 Document Type Management

#### 3.1.1 Create Document Type
**User Story**: As a user, I want to create a new document type so I can extract structured data from similar documents.

**Acceptance Criteria**:
- User can name the document type (e.g., "Invoice", "Receipt", "W2 Form")
- User can add a description and tags for organization
- System generates unique identifier for document type
- Document type appears in user's dashboard

**Technical Requirements**:
- Database schema for document types
- CRUD API endpoints
- Form validation and error handling

#### 3.1.2 Define Extraction Schema
**User Story**: As a user, I want to define which fields to extract so the system knows what information I need.

**Acceptance Criteria**:
- User can add unlimited fields to schema
- Each field has:
  - Field name (required)
  - Field description (optional but recommended)
  - Data type (text, number, date, currency, email, phone, address, etc.)
  - Validation rules (regex pattern, min/max, required/optional)
  - Expected format/examples
- User can organize fields into groups/sections
- User can reorder fields via drag-and-drop
- System validates schema before saving

**Field Configuration Options**:
```json
{
  "field_name": "invoice_number",
  "display_name": "Invoice Number",
  "description": "Unique identifier for the invoice, typically alphanumeric",
  "data_type": "text",
  "required": true,
  "validation": {
    "pattern": "^INV-[0-9]{6}$",
    "example": "INV-123456"
  },
  "extraction_hints": [
    "Often appears in top-right corner",
    "May be labeled as 'Invoice #', 'Inv No.', or 'Reference'"
  ]
}
```

**Technical Requirements**:
- JSON schema storage
- Schema validation engine
- Type system supporting common business data types
- Visual schema builder UI component

#### 3.1.3 Upload Ground Truth Documents
**User Story**: As a user, I want to provide example documents with correct values so the system can learn my extraction patterns.

**Acceptance Criteria**:
- User can upload documents (PDF, PNG, JPG, TIFF)
- System performs OCR on uploaded documents
- User sees OCR-extracted text alongside original document
- User can annotate/label extracted values for each field
- User can draw bounding boxes on document for field locations (optional)
- System requires minimum 3-5 ground truth examples per document type
- User can add more examples over time to improve accuracy

**Annotation Interface**:
- Split-view: Document preview | Extraction form
- Highlight text in OCR output to auto-populate fields
- Copy-paste from OCR text
- Manual entry if OCR missed text
- Confidence indicator for OCR quality
- Save as ground truth example

**Technical Requirements**:
- File upload with size limits (max 10MB per file)
- Azure Document Intelligence API integration
- OCR result caching
- Annotation data storage
- Bounding box coordinates storage (for future improvement)

### 3.2 Pipeline Generation & Optimization

#### 3.2.1 DSPy Pipeline Creation
**User Story**: As a user, I want the system to automatically generate an extraction pipeline from my schema and examples.

**Acceptance Criteria**:
- User clicks "Generate Pipeline" button
- System creates DSPy modules for extraction
- System compiles pipeline with initial prompts
- User sees pipeline architecture visualization
- System runs initial test on ground truth examples

**Pipeline Architecture**:
```python
class OCRDocumentExtractor(dspy.Module):
    """Main extraction pipeline"""

    def __init__(self, schema):
        self.schema = schema
        self.ocr_preprocessor = OCRPreprocessor()
        self.field_extractors = {
            field.name: dspy.ChainOfThought(f"ocr_text, field_definition -> {field.name}")
            for field in schema.fields
        }
        self.validator = SchemaValidator(schema)
        self.consolidator = ResultConsolidator()

    def forward(self, document):
        # 1. OCR preprocessing
        ocr_text = self.ocr_preprocessor(document)

        # 2. Individual field extraction
        extracted_fields = {}
        for field_name, extractor in self.field_extractors.items():
            field_def = self.schema.get_field(field_name)
            extracted_fields[field_name] = extractor(
                ocr_text=ocr_text,
                field_definition=field_def.to_prompt()
            )

        # 3. Validation and error correction
        validated_fields = self.validator(extracted_fields)

        # 4. Result consolidation
        return self.consolidator(validated_fields)
```

**Technical Requirements**:
- DSPy module factory based on schema
- Prompt template generation
- Pipeline serialization/deserialization
- Background job for pipeline generation

#### 3.2.2 GEPA Optimization
**User Story**: As a user, I want the system to automatically optimize extraction accuracy using my ground truth examples.

**Acceptance Criteria**:
- User initiates optimization with "Optimize Pipeline" button
- System uses GEPA optimizer with ground truth examples as training set
- User sees real-time optimization progress:
  - Current iteration number
  - Best accuracy achieved so far
  - Estimated time remaining
- System runs for configurable iterations (default: 10-20)
- User can stop optimization early if satisfied
- System saves best-performing pipeline version
- User can compare before/after accuracy

**GEPA Configuration**:
```python
from dspy.teleprompt import GEPA

optimizer = GEPA(
    metric=extraction_accuracy_metric,
    breadth=10,  # Number of candidate variations per iteration
    depth=15,    # Number of optimization iterations
    max_bootstrapped_demos=5,  # Few-shot examples per prompt
    max_labeled_demos=10,      # Max ground truth examples to use
)

# Optimize the pipeline
optimized_pipeline = optimizer.compile(
    student=document_extractor,
    trainset=ground_truth_examples,
    valset=validation_examples,  # 20% holdout
)
```

**Optimization Metrics**:
- **Field-level accuracy**: % of fields extracted correctly
- **Document-level accuracy**: % of documents with all fields correct
- **Confidence score**: Model confidence in extractions
- **Validation pass rate**: % passing schema validation

**Technical Requirements**:
- GEPA optimizer integration
- Custom metric functions for structured extraction
- Async job processing for long-running optimization
- Progress tracking and WebSocket updates
- Model versioning and comparison
- Automatic validation set creation (80/20 split)

#### 3.2.3 Feedback-Driven Improvement
**User Story**: As a user, I want to correct extraction errors and have the system learn from my corrections.

**Acceptance Criteria**:
- User processes documents and sees extraction results
- User can mark fields as correct/incorrect
- User can provide corrected values for incorrect fields
- User can provide textual feedback (e.g., "Invoice number is always in top-right")
- System stores corrections as new training examples
- User can trigger re-optimization with accumulated feedback
- System shows improvement metrics after re-optimization

**Feedback Types**:
1. **Binary feedback**: Thumbs up/down per field
2. **Correction feedback**: Provide correct value
3. **Textual feedback**: Natural language guidance
4. **Structural feedback**: "This field type should be date, not text"

**GEPA Feedback Integration**:
```python
# GEPA accepts textual feedback for optimization
feedback_examples = [
    {
        "document": doc1,
        "predicted": {"invoice_number": "123456"},
        "correct": {"invoice_number": "INV-123456"},
        "feedback": "Invoice number always has 'INV-' prefix"
    },
    {
        "document": doc2,
        "predicted": {"total": "1,234.56 USD"},
        "correct": {"total": 1234.56},
        "feedback": "Remove currency symbols and convert to float"
    }
]

# Re-optimize with feedback
optimized_pipeline = optimizer.compile(
    student=current_pipeline,
    trainset=ground_truth_examples + corrections,
    feedback=feedback_examples  # GEPA leverages this!
)
```

**Technical Requirements**:
- Correction storage and versioning
- Feedback aggregation and prioritization
- Incremental re-training capability
- A/B testing framework for pipeline versions

### 3.3 Document Processing

#### 3.3.1 Single Document Processing
**User Story**: As a user, I want to upload a document and extract structured data using my trained pipeline.

**Acceptance Criteria**:
- User selects document type
- User uploads document (PDF/image)
- System performs OCR
- System runs extraction pipeline
- User sees extracted data in structured form
- User sees confidence scores per field
- User can view source document with highlighted extraction regions
- User can export results (JSON, CSV, Excel)
- User can correct and provide feedback

**Results Display**:
```
┌─────────────────────────────────────────┐
│ Invoice Extraction Results             │
├─────────────────────────────────────────┤
│ Invoice Number: INV-123456  ✓ (98%)    │
│ Date: 2025-10-15           ✓ (95%)    │
│ Vendor: ACME Corp          ✓ (99%)    │
│ Total: $1,234.56           ⚠ (78%)    │
│                                         │
│ [Approve] [Correct Errors] [Reject]    │
└─────────────────────────────────────────┘
```

**Technical Requirements**:
- Real-time processing API
- Confidence score calculation
- Result rendering with validation status
- Export functionality (multiple formats)

#### 3.3.2 Batch Processing
**User Story**: As a user, I want to process hundreds of documents at once so I can automate my workflow.

**Acceptance Criteria**:
- User uploads ZIP file or multiple files
- System queues documents for processing
- User sees batch processing dashboard:
  - Total documents
  - Processed count
  - Success/failure rate
  - Average confidence score
- User can download batch results as CSV/Excel
- User can review low-confidence extractions
- System handles failures gracefully

**Batch Processing Flow**:
```
Upload → Queue → Process → Validate → Results
         ↓
      Priority Queue
         ↓
    Worker Pool (5-10 concurrent)
         ↓
      Results Database
         ↓
      Download Center
```

**Technical Requirements**:
- Async job queue (Celery/Redis)
- Worker pool management
- Progress tracking
- Batch result aggregation
- Error handling and retry logic

#### 3.3.3 API Integration
**User Story**: As a developer, I want to integrate document extraction into my existing systems via API.

**Acceptance Criteria**:
- User can generate API key from dashboard
- API documentation available
- RESTful endpoints for:
  - Upload document
  - Check processing status
  - Retrieve extraction results
  - Provide feedback
- Webhook support for async processing
- Rate limiting and authentication

**API Endpoints**:
```
POST   /api/v1/extract
POST   /api/v1/extract/batch
GET    /api/v1/jobs/{job_id}
GET    /api/v1/results/{result_id}
POST   /api/v1/feedback
GET    /api/v1/document-types
```

**Example API Usage**:
```bash
curl -X POST https://ocrmate.ai/api/v1/extract \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "document=@invoice.pdf" \
  -F "document_type_id=dt_abc123"
```

**Technical Requirements**:
- API key management
- Rate limiting (100 requests/min per user)
- OpenAPI/Swagger documentation
- Webhook delivery system
- API usage analytics

### 3.4 Pipeline Management

#### 3.4.1 Version Control
**User Story**: As a user, I want to track different versions of my extraction pipeline so I can roll back if needed.

**Acceptance Criteria**:
- System automatically versions pipeline on each optimization
- User sees version history with:
  - Version number
  - Accuracy metrics
  - Creation timestamp
  - Number of training examples used
- User can compare versions side-by-side
- User can promote any version to "production"
- User can test different versions on same document

**Technical Requirements**:
- Pipeline serialization and storage
- Version metadata tracking
- Diff visualization
- Version rollback mechanism

#### 3.4.2 Performance Monitoring
**User Story**: As a user, I want to monitor extraction performance over time to ensure quality.

**Acceptance Criteria**:
- Dashboard showing:
  - Extraction accuracy trend
  - Processing volume (docs/day)
  - Average confidence scores
  - Field-level accuracy breakdown
  - Common failure patterns
- Alerts for accuracy drops
- Export performance reports

**Metrics Dashboard**:
```
Last 30 Days:
- Documents processed: 15,234
- Average accuracy: 94.2% (↑2.1%)
- Average processing time: 3.2s
- Fields with >90% accuracy: 12/15

Top Errors:
1. Date format variations (8% of errors)
2. Multi-line addresses (5% of errors)
3. Currency symbol confusion (3% of errors)
```

**Technical Requirements**:
- Time-series metrics storage
- Alerting system
- Analytics dashboard
- Report generation

#### 3.4.3 Prompt & Code Export
**User Story**: As a developer, I want to export optimized prompts and code to use in my own systems.

**Acceptance Criteria**:
- User can export:
  - DSPy pipeline code (Python)
  - Optimized prompts (text files)
  - LangChain equivalent code
  - OpenAI API equivalent
- Export includes:
  - Schema definition
  - Prompt templates
  - Few-shot examples
  - Validation logic
- Code is documented and runnable

**Export Formats**:
1. **DSPy Native** (Python package)
2. **Standalone Python** (minimal dependencies)
3. **OpenAI API calls** (curl/Python/JavaScript)
4. **LangChain** (Python)
5. **Prompt templates** (Markdown/JSON)

**Technical Requirements**:
- Code generation templates
- Dependency management
- Export packaging
- Documentation generation

---

## 4. Technical Architecture

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   React     │  │  Document    │  │  Pipeline    │       │
│  │   Web App   │  │  Viewer      │  │  Builder     │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↕ REST API / WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   API    │  │  Pipeline│  │  GEPA    │  │  Metrics │   │
│  │  Server  │  │  Engine  │  │ Optimizer│  │  Service │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      Processing Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   OCR    │  │  DSPy    │  │  Job     │  │  Cache   │   │
│  │  Service │  │  Runtime │  │  Queue   │  │  Layer   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │   Redis  │  │   S3/    │  │  Vector  │   │
│  │    DB    │  │   Cache  │  │  Blob    │  │    DB    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     External Services                        │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Azure Document  │  │   OpenAI     │  │   LiteLLM    │  │
│  │  Intelligence   │  │     API      │  │   Gateway    │  │
│  └─────────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack

#### 4.2.1 Frontend
- **Framework**: React 18+ with TypeScript
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: Zustand or Redux Toolkit
- **PDF Viewer**: react-pdf or PDF.js
- **Forms**: React Hook Form + Zod validation
- **File Upload**: react-dropzone
- **Data Grid**: TanStack Table
- **Charts**: Recharts or Chart.js

#### 4.2.2 Backend
- **Framework**: FastAPI (Python 3.12+)
- **LLM Framework**: DSPy 3.0+
- **LLM Gateway**: LiteLLM
- **OCR Service**: Azure Document Intelligence
- **Task Queue**: Celery + Redis
- **Caching**: Redis
- **API Documentation**: FastAPI auto-generated OpenAPI

#### 4.2.3 Database
- **Primary DB**: PostgreSQL 15+
  - User accounts
  - Document types & schemas
  - Ground truth examples
  - Extraction results
  - Audit logs
- **Vector DB**: Pinecone or Weaviate (for semantic search)
  - Similar document matching
  - Example retrieval for few-shot
- **Object Storage**: AWS S3 or Azure Blob
  - Uploaded documents
  - OCR results
  - Pipeline artifacts

#### 4.2.4 Infrastructure
- **Container**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Error Tracking**: Sentry

### 4.3 Data Models

#### 4.3.1 Core Entities

```python
# User
class User:
    id: UUID
    email: str
    name: str
    organization_id: UUID
    created_at: datetime
    api_keys: List[APIKey]

# Document Type
class DocumentType:
    id: UUID
    name: str
    description: str
    schema: ExtractionSchema
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    tags: List[str]

# Extraction Schema
class ExtractionSchema:
    version: int
    fields: List[FieldDefinition]
    validation_rules: List[ValidationRule]

class FieldDefinition:
    name: str
    display_name: str
    description: str
    data_type: DataType  # text, number, date, currency, etc.
    required: bool
    validation: Optional[FieldValidation]
    extraction_hints: List[str]

# Ground Truth Example
class GroundTruthExample:
    id: UUID
    document_type_id: UUID
    document_url: str  # S3/Blob storage
    ocr_text: str
    labeled_values: Dict[str, Any]  # field_name -> value
    bounding_boxes: Optional[Dict[str, BBox]]
    created_at: datetime
    created_by: UUID

# Pipeline
class Pipeline:
    id: UUID
    document_type_id: UUID
    version: int
    dspy_program: bytes  # Serialized DSPy module
    prompts: Dict[str, str]  # field_name -> prompt
    metrics: PipelineMetrics
    status: PipelineStatus  # draft, training, optimized, production
    created_at: datetime
    parent_version_id: Optional[UUID]

class PipelineMetrics:
    field_accuracies: Dict[str, float]
    overall_accuracy: float
    avg_confidence: float
    training_examples_count: int
    optimization_iterations: int

# Extraction Job
class ExtractionJob:
    id: UUID
    document_type_id: UUID
    pipeline_id: UUID
    document_url: str
    status: JobStatus  # queued, processing, completed, failed
    result: Optional[ExtractionResult]
    created_at: datetime
    completed_at: Optional[datetime]

class ExtractionResult:
    job_id: UUID
    extracted_fields: Dict[str, FieldExtraction]
    validation_status: ValidationStatus
    overall_confidence: float

class FieldExtraction:
    value: Any
    confidence: float
    source_location: Optional[BBox]
    validated: bool
    validation_errors: List[str]

# Feedback
class UserFeedback:
    id: UUID
    job_id: UUID
    field_name: str
    predicted_value: Any
    corrected_value: Optional[Any]
    feedback_type: FeedbackType  # correction, textual, thumbs_up/down
    textual_feedback: Optional[str]
    created_at: datetime
```

### 4.4 Security & Privacy

#### 4.4.1 Authentication & Authorization
- **Auth Provider**: Auth0 or Firebase Auth
- **Authentication**: JWT tokens
- **Authorization**: Role-based access control (RBAC)
  - Owner: Full access to document types
  - Editor: Can modify schemas and train pipelines
  - Viewer: Can only view and process documents
  - API User: Programmatic access only
- **Multi-tenancy**: Organization-level data isolation

#### 4.4.2 Data Security
- **Encryption at rest**: AES-256 for stored documents
- **Encryption in transit**: TLS 1.3 for all API calls
- **Document retention**: Configurable auto-deletion (30/60/90 days)
- **PII detection**: Automatic redaction options
- **Audit logging**: Complete audit trail for compliance

#### 4.4.3 API Security
- **Rate limiting**: 100 requests/min per user, 1000/min per organization
- **API key rotation**: Support for key rotation without downtime
- **IP whitelisting**: Optional IP restrictions
- **Webhook signing**: HMAC signature verification

---

## 5. User Experience & Interface Design

### 5.1 Navigation Structure

```
Dashboard
├── Document Types
│   ├── Create New
│   ├── My Document Types
│   │   └── [Document Type]
│   │       ├── Schema Editor
│   │       ├── Ground Truth Examples
│   │       ├── Pipeline Optimization
│   │       ├── Test & Validate
│   │       └── Performance Analytics
│   └── Templates (pre-built types)
│
├── Process Documents
│   ├── Single Upload
│   ├── Batch Upload
│   └── Processing History
│
├── Results
│   ├── Recent Extractions
│   ├── Review Queue (low confidence)
│   └── Export Center
│
├── API & Integration
│   ├── API Keys
│   ├── Documentation
│   ├── Webhooks
│   └── Code Export
│
└── Settings
    ├── Account
    ├── Billing
    └── Team Management
```

### 5.2 Key User Flows

#### 5.2.1 First-Time User Flow
1. **Sign Up** → Email verification
2. **Onboarding Tutorial** → Interactive guide
3. **Choose Template or Start Fresh**
4. **Upload 3 Example Documents** → Quick start
5. **Auto-generate Schema** → AI suggests fields
6. **Review & Edit Schema**
7. **Label Ground Truth**
8. **Generate Pipeline** → 2-3 minutes
9. **Test on New Document** → Instant feedback
10. **Success!** → Process more or refine

#### 5.2.2 Schema Creation Flow
```
Create Document Type
    ↓
Name & Describe
    ↓
Add Fields (one-by-one or bulk import)
    ↓
Configure Field Properties
    ↓
Set Validation Rules
    ↓
Preview Schema
    ↓
Save & Continue to Examples
```

#### 5.2.3 Optimization Flow
```
Upload Ground Truth (min 3-5)
    ↓
Label Each Example
    ↓
Click "Optimize Pipeline"
    ↓
GEPA Runs (10-20 iterations)
    ↓
See Real-time Progress
    ↓
Review Metrics
    ↓
Test on Validation Set
    ↓
Approve or Re-optimize with Feedback
    ↓
Promote to Production
```

### 5.3 Wireframes (Key Screens)

#### 5.3.1 Model Selection (Inspired by LangStruct)
```
┌──────────────────────────────────────────────────────────┐
│ Pipeline Configuration                                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Select Language Model                                    │
│                                                           │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Model Family: [OpenAI ▼]                         │   │
│ │                                                   │   │
│ │ Model: [gpt-4o                            ▼]     │   │
│ │                                                   │   │
│ │ • gpt-4o                                          │   │
│ │ • gpt-4-turbo                                     │   │
│ │ • gpt-3.5-turbo                                   │   │
│ └──────────────────────────────────────────────────┘   │
│                                                           │
│ Other Providers:                                         │
│ [ Anthropic ] [ Google ] [ Local Models ] [ Custom ]    │
│                                                           │
│ Performance Estimates:                                   │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Model         │ Accuracy │ Speed │ Cost/Doc      │   │
│ ├──────────────────────────────────────────────────┤   │
│ │ gpt-4o        │   95%    │ 3.2s  │ $0.08        │   │
│ │ gpt-4-turbo   │   94%    │ 2.8s  │ $0.12        │   │
│ │ claude-3.5    │   96%    │ 3.5s  │ $0.09        │   │
│ │ gemini-pro    │   93%    │ 2.1s  │ $0.04        │   │
│ └──────────────────────────────────────────────────┘   │
│                                                           │
│ ⚠ Changing model will re-optimize pipeline (~15 min)    │
│                                                           │
│                           [Switch Model] [Cancel]        │
└──────────────────────────────────────────────────────────┘
```

#### 5.3.2 Schema Editor
```
┌──────────────────────────────────────────────────────────┐
│ Invoice Schema Editor                    [Save] [Cancel] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Document Type Information                                │
│ Name: [Invoice                           ]               │
│ Description: [Standard vendor invoices   ]               │
│                                                           │
│ Extraction Fields                        [+ Add Field]   │
│                                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 1. Invoice Number                    [Edit] [Delete]│  │
│ │    Type: Text | Required: ☑ | Pattern: INV-\d{6}   │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 2. Date                              [Edit] [Delete]│  │
│ │    Type: Date | Required: ☑ | Format: YYYY-MM-DD   │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 3. Vendor Name                       [Edit] [Delete]│  │
│ │    Type: Text | Required: ☑                         │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
│ [+ Add Field] [Import from Template]                     │
│                                                           │
│                           [Next: Add Examples →]          │
└──────────────────────────────────────────────────────────┘
```

#### 5.3.2 Ground Truth Annotation
```
┌──────────────────────────────────────────────────────────────┐
│ Label Example 1 of 5                   [Save & Next] [Skip] │
├─────────────────────────┬────────────────────────────────────┤
│                         │                                    │
│  Document Preview       │  Extraction Form                   │
│                         │                                    │
│  ┌───────────────────┐ │  Invoice Number                    │
│  │                   │ │  [INV-123456          ] ✓          │
│  │   [Invoice PDF]   │ │                                    │
│  │                   │ │  Date                              │
│  │                   │ │  [2025-10-15          ] ✓          │
│  │                   │ │                                    │
│  │                   │ │  Vendor Name                       │
│  │   Zoom: [100%]    │ │  [ACME Corporation    ] ✓          │
│  │                   │ │                                    │
│  └───────────────────┘ │  Total Amount                      │
│                         │  [$1,234.56           ] ⚠          │
│  OCR Text (click to    │  Confidence: 78% - Please verify   │
│  copy):                 │                                    │
│                         │  [Clear All] [Auto-fill from OCR] │
│  "Invoice #INV-123456  │                                    │
│   Date: 10/15/2025     │                                    │
│   From: ACME Corp...   │                                    │
│                         │                                    │
├─────────────────────────┴────────────────────────────────────┤
│ Progress: ████░░░░░░ 2/5 examples labeled                    │
└──────────────────────────────────────────────────────────────┘
```

#### 5.3.3 Optimization Dashboard
```
┌──────────────────────────────────────────────────────────┐
│ Pipeline Optimization: Invoice v2                        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Status: Optimizing... (Iteration 8/15)      [Stop]       │
│                                                           │
│ Progress: ████████████░░░ 53%                            │
│ Est. time remaining: 2 min 15 sec                        │
│                                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │  Accuracy Trend                                     │  │
│ │                                                     │  │
│ │  95% ┤                                        ●     │  │
│ │  90% ┤                              ●     ●        │  │
│ │  85% ┤                    ●     ●                  │  │
│ │  80% ┤          ●     ●                            │  │
│ │  75% ┤     ●                                       │  │
│ │      └─────┬─────┬─────┬─────┬─────┬─────┬────    │  │
│ │            2     4     6     8    10    12         │  │
│ │                  Iterations                         │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
│ Current Best Metrics:                                    │
│ • Overall Accuracy: 92.4%                                │
│ • Invoice Number: 98% ✓                                  │
│ • Date: 95% ✓                                            │
│ • Vendor: 99% ✓                                          │
│ • Total: 89% ⚠                                           │
│                                                           │
│ Training Examples Used: 5                                │
│ Validation Accuracy: 91.2%                               │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

#### 5.3.4 Results with Source Attribution (Inspired by LangStruct)
```
┌──────────────────────────────────────────────────────────────┐
│ Extraction Results: Invoice_2024_001.pdf      [Export] [✓]  │
├─────────────────────────┬────────────────────────────────────┤
│                         │                                    │
│  Source Document        │  Extracted Data                    │
│                         │                                    │
│  ┌───────────────────┐ │  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  │                   │ │  ┃ Invoice Number              ┃    │
│  │   Invoice #:      │ │  ┃ INV-123456         98% ✓   ┃    │
│  │   ████████████    │ │  ┃ 📍 Source: Line 3, top-right ┃    │
│  │   ^^^highlighted  │ │  ┃    "Invoice #: INV-123456"  ┃    │
│  │                   │ │  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│  │                   │ │                                    │
│  │   Date:           │ │  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  │   ████████        │ │  ┃ Date                        ┃    │
│  │   10/15/2025      │ │  ┃ 2025-10-15         95% ✓   ┃    │
│  │   ^^^highlighted  │ │  ┃ 📍 Source: Line 5           ┃    │
│  │                   │ │  ┃    "Date: 10/15/2025"       ┃    │
│  │   Total: $1,234   │ │  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│  │   ████████        │ │                                    │
│  │   ^^^highlighted  │ │  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  └───────────────────┘ │  ┃ Total Amount                ┃    │
│                         │  ┃ $1,234.56          89% ⚠   ┃    │
│  Hover over fields →   │  ┃ 📍 Source: Bottom right     ┃    │
│  to highlight source    │  ┃    "Total: $1,234"          ┃    │
│                         │  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│  [← Previous] [Next →] │                                    │
│                         │  [Approve All] [Correct Errors]    │
│                         │                                    │
│  💡 Click any field to highlight source in document         │
│  💡 Hover over highlighted text to see which field          │
└─────────────────────────┴────────────────────────────────────┘
```

**Source Attribution Features** (Like LangStruct):
- Yellow highlight on document when field is selected
- Bounding box coordinates stored for each extraction
- Exact text span shown in field details
- Interactive: click field → see source, click source → see field
- Builds user trust through transparency

---

## 6. Development Roadmap

### 6.1 Phase 1: MVP (Months 1-3)

**Goal**: Basic working product for single document type

**Features**:
- ✓ User authentication (Auth0)
- ✓ Create single document type
- ✓ Define extraction schema (up to 20 fields)
- ✓ Upload and label 5 ground truth examples
- ✓ Azure Document Intelligence OCR integration
- ✓ Basic DSPy pipeline generation
- ✓ GEPA optimization (10 iterations max)
- ✓ Single document processing
- ✓ Results display with confidence scores
- ✓ Basic feedback mechanism

**Success Criteria**:
- 10 beta users successfully create pipelines
- Average 85%+ extraction accuracy
- Pipeline generation time < 5 minutes

### 6.2 Phase 2: Core Features (Months 4-6)

**Features**:
- ✓ Multiple document types per user
- ✓ Batch processing (up to 100 docs)
- ✓ Advanced schema validation
- ✓ Field-level confidence scores
- ✓ Pipeline versioning
- ✓ Performance analytics dashboard
- ✓ Export results (JSON, CSV, Excel)
- ✓ Template library (10 common document types)
- ✓ Improved feedback and re-optimization
- ✓ Team collaboration (shared document types)

**Success Criteria**:
- 100 active users
- 90%+ extraction accuracy on common documents
- 1000+ documents processed daily

### 6.3 Phase 3: Scale & Polish (Months 7-9)

**Features**:
- ✓ REST API with authentication
- ✓ API documentation (OpenAPI/Swagger)
- ✓ Webhook support
- ✓ Advanced GEPA configuration options
- ✓ Multi-page document support
- ✓ Table extraction
- ✓ Handwriting recognition
- ✓ Custom validation rules engine
- ✓ Pipeline export (code generation)
- ✓ Advanced monitoring and alerting

**Success Criteria**:
- 500 active users
- 50+ API integrations
- 10,000+ documents processed daily
- 95%+ uptime

### 6.4 Phase 4: Enterprise (Months 10-12)

**Features**:
- ✓ SSO integration (SAML, OAuth)
- ✓ On-premise deployment option
- ✓ Advanced RBAC
- ✓ Audit logging and compliance reports
- ✓ Custom LLM integration (bring your own model)
- ✓ Advanced vector search for similar documents
- ✓ Multi-language support
- ✓ White-labeling options
- ✓ SLA guarantees
- ✓ Dedicated support

**Success Criteria**:
- 10+ enterprise customers
- 100,000+ documents processed daily
- 99.9% uptime
- SOC2 compliance achieved

---

## 7. Non-Functional Requirements

### 7.1 Performance
- **OCR Processing**: < 5 seconds per page
- **Pipeline Generation**: < 5 minutes for initial pipeline
- **GEPA Optimization**: < 15 minutes for 15 iterations
- **Single Document Extraction**: < 10 seconds
- **API Response Time**: < 2 seconds (p95)
- **Batch Processing**: 100 documents/hour minimum

### 7.2 Scalability
- **Concurrent Users**: Support 1000+ simultaneous users
- **Document Storage**: Unlimited (via object storage)
- **Pipeline Storage**: 100+ versions per document type
- **Horizontal Scaling**: Auto-scale workers based on queue depth

### 7.3 Reliability
- **Uptime**: 99.5% (MVP), 99.9% (Enterprise)
- **Data Durability**: 99.999999999% (S3/Blob standard)
- **Backup**: Daily automated backups
- **Disaster Recovery**: RPO < 1 hour, RTO < 4 hours

### 7.4 Usability
- **Onboarding Time**: < 30 minutes to first successful extraction
- **Learning Curve**: Non-technical users can create pipelines
- **Mobile Responsiveness**: Works on tablets (iPad+)
- **Browser Support**: Chrome, Firefox, Safari, Edge (latest 2 versions)

### 7.5 Maintainability
- **Code Coverage**: > 80% test coverage
- **Documentation**: Comprehensive API and user documentation
- **Monitoring**: Real-time metrics and alerting
- **Deployment**: Zero-downtime deployments

---

## 8. Success Metrics & KPIs

### 8.1 Product Metrics
- **User Activation**: % of users who create first pipeline (Target: 70%)
- **Time to Value**: Time from signup to first successful extraction (Target: < 1 hour)
- **Pipeline Creation Success**: % of pipelines achieving >85% accuracy (Target: 80%)
- **User Retention**: Weekly active users (Target: 60% WAU/MAU ratio)
- **Document Processing Volume**: Documents processed per user per month (Target: 500+)

### 8.2 Technical Metrics
- **Extraction Accuracy**: Average field-level accuracy (Target: 90%+)
- **API Uptime**: System availability (Target: 99.5%+)
- **Processing Speed**: Average extraction time (Target: < 10s)
- **Error Rate**: Failed extractions (Target: < 5%)
- **GEPA Improvement**: Accuracy lift from optimization (Target: +10% average)

### 8.3 Business Metrics
- **Monthly Recurring Revenue (MRR)**: Recurring revenue
- **Customer Acquisition Cost (CAC)**: Cost to acquire customer
- **Lifetime Value (LTV)**: Customer lifetime value
- **Churn Rate**: Monthly user churn (Target: < 5%)
- **Net Promoter Score (NPS)**: User satisfaction (Target: 40+)

---

## 9. Pricing & Monetization

### 9.1 Pricing Tiers

#### Free Tier
- 1 document type
- 100 documents/month
- Basic templates
- Community support
- **Price**: $0/month

#### Professional Tier
- 10 document types
- 2,000 documents/month
- Advanced optimization (20 iterations)
- Priority support
- API access (1000 calls/month)
- **Price**: $49/month

#### Business Tier
- Unlimited document types
- 10,000 documents/month
- Custom GEPA configuration
- Team collaboration (5 users)
- API access (10,000 calls/month)
- Webhooks
- **Price**: $199/month

#### Enterprise Tier
- Everything in Business
- Unlimited documents
- Unlimited users
- SSO integration
- On-premise deployment option
- SLA guarantees
- Dedicated support
- **Price**: Custom (starting at $999/month)

### 9.2 Add-ons
- **Extra Documents**: $0.01 per document beyond plan limit
- **Additional Users**: $20/user/month
- **Advanced Support**: $500/month
- **Custom Training**: $2000 one-time

---

## 10. Risks & Mitigations

### 10.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OCR accuracy insufficient | High | Medium | Multi-provider OCR fallback, human-in-loop review |
| GEPA optimization too slow | Medium | Low | Async processing, progress indicators, iteration limits |
| LLM API costs too high | High | Medium | Caching, smaller models for simple tasks, batch processing |
| Pipeline drift over time | Medium | Medium | Continuous monitoring, automated retraining, alerts |
| Data privacy concerns | High | Medium | SOC2 compliance, encryption, auto-deletion options |

### 10.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low user adoption | High | Medium | Extensive beta testing, templates, excellent onboarding |
| Competitors with better accuracy | High | Low | Continuous GEPA improvements, unique UX, fast iteration |
| Pricing too high/low | Medium | Medium | Market research, tiered pricing, usage-based billing |
| Scaling costs | High | Medium | Efficient architecture, caching, cost monitoring |

### 10.3 Regulatory Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GDPR/CCPA compliance | High | High | Privacy by design, data retention policies, DPO |
| Document retention laws | Medium | Medium | Configurable retention, legal review |
| AI regulation changes | Medium | Low | Monitor regulations, adaptable architecture |

---

## 11. Open Questions & Future Considerations

### 11.1 Open Questions
1. Should we support custom LLM models (e.g., fine-tuned models)?
2. How to handle multi-language documents in MVP?
3. Should table extraction be in Phase 1 or Phase 3?
4. What's the optimal number of ground truth examples to require?
5. Should we offer document preprocessing (deskewing, denoising)?

### 11.2 Future Enhancements (Post-v1)
- **Active learning**: System suggests which documents to label for maximum improvement
- **Cross-document validation**: Extract and validate related documents (PO + Invoice matching)
- **Natural language schema creation**: "Extract invoice number, date, and total" → auto-generate schema
- **Document classification**: Auto-route documents to correct extraction pipeline
- **Collaborative labeling**: Team-based annotation workflows
- **Model marketplace**: Share/sell optimized pipelines
- **Integration marketplace**: Pre-built connectors for ERP/CRM systems
- **Mobile app**: Process documents from phone camera
- **Email integration**: Process attachments from email
- **Smart suggestions**: AI recommends schema fields based on document analysis

---

## 12. Appendices

### 12.1 Glossary
- **GEPA**: Genetic-Pareto optimizer for DSPy, uses reflective prompt evolution
- **DSPy**: Framework for programming (not prompting) language models
- **Ground Truth**: Human-labeled correct extraction values for training
- **Pipeline**: Complete extraction workflow from OCR to validated output
- **Field**: Individual data point to extract (e.g., invoice number)
- **Schema**: Complete definition of all fields for a document type
- **Confidence Score**: Model's certainty about extracted value (0-100%)

### 12.2 References
- DSPy Documentation: https://dspy.ai
- GEPA Paper: "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning" (Agrawal et al., 2025)
- Azure Document Intelligence: https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence
- LiteLLM: https://litellm.ai

### 12.3 Competitive Analysis

#### LangStruct (https://langstruct.dev/)
- **Strengths**: DSPy automation, model flexibility, source tracing, developer focus
- **Weaknesses**: Text-only (no document OCR), technical users only, unclear pricing
- **Target Market**: Developers needing structured text extraction
- **Pricing**: Unknown

**Our Advantages over LangStruct**:
1. Full document pipeline (OCR + extraction, not just text)
2. Business user interface (no coding required)
3. GEPA optimization (textual feedback + Pareto frontier)
4. Visual annotation and validation workflows
5. Enterprise features (team collaboration, SSO, audit logs)
6. Document-specific features (multi-page, tables, handwriting)

**What We Learn from LangStruct**:
1. Model agnosticism is a key differentiator - ADOPT
2. "No prompt engineering" messaging resonates - ADOPT
3. Source attribution builds trust - ADOPT
4. Developer API must be clean and simple - ADOPT

#### Other Competitors
- **Nanonets**: Strong OCR, limited customization, expensive
- **Docparser**: Template-based, not ML-powered, dated approach
- **Rossum**: Enterprise-focused, very expensive, long sales cycles
- **Amazon Textract**: API-only, requires coding, AWS lock-in
- **Google Document AI**: Good accuracy, complex setup, expensive

**Our Unique Differentiators**:
1. Zero-code pipeline creation (vs Textract, Document AI)
2. GEPA-powered continuous optimization (vs everyone)
3. Multi-model flexibility like LangStruct (vs vendor lock-in)
4. Source attribution on documents (vs black-box OCR)
5. Both UI and API (vs LangStruct API-only or Nanonets UI-only)
6. Affordable pricing for SMBs (vs enterprise-only)

---

## 13. Conclusion

OCR Mate represents a unique opportunity to democratize structured document extraction by combining:
- **Cutting-edge AI**: GEPA optimizer + DSPy framework
- **User-friendly design**: Zero-code interface for business users
- **Developer-friendly**: API + code export for technical users
- **Continuous improvement**: Learn from feedback over time

By following this requirements document, we can build a product that serves both non-technical business users and technical developers, creating a platform that grows more accurate and valuable with every document processed.

**Next Steps**:
1. Technical feasibility validation (GEPA integration POC)
2. User research & validation (interviews with 10-20 target users)
3. UI/UX design (high-fidelity mockups)
4. Architecture review (scaling & cost estimates)
5. MVP development kickoff

---

**Document Status**: Draft for Review
**Last Updated**: October 2025
**Owner**: Product Team
**Reviewers**: Engineering, Design, Business
