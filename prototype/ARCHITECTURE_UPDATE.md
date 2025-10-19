# Architecture Update - Document-Centric Design

## ✅ What Changed

Based on user feedback, the prototype has been refactored to use a **document-centric architecture** where schema, examples, pipeline, and analytics are all **local to each document type**.

---

## Old Architecture (Incorrect)

```
Dashboard
├── Schema Editor (global, not tied to document type) ❌
├── Annotation (global) ❌
├── Optimization (global) ❌
└── Results (global)
```

**Problem**: Schema editor and other features were standalone pages, not scoped to a specific document type.

---

## New Architecture (Correct) ✅

```
Dashboard
├── Document Types (list)
│   └── [Specific Document Type] ← Each type is independent!
│       ├── Schema Tab (local to this type)
│       ├── Ground Truth Tab (local to this type)
│       ├── Pipeline & Optimization Tab (local to this type)
│       └── Analytics Tab (local to this type)
├── Process Documents (use any document type)
└── Settings (global)
```

**Benefits**:
- ✅ Each document type is **completely independent**
- ✅ Different document types can have different schemas, models, examples
- ✅ Clear hierarchy: Document Type → Properties
- ✅ Easier to understand and navigate

---

## New Page Structure

### Main Pages:
1. **[index.html](index.html)** - Dashboard with quick stats
2. **[document-types.html](document-types.html)** - List all document types
3. **[document-type-invoice.html](document-type-invoice.html)** - Invoice detail with tabs ⭐
4. **[01-model-selector.html](01-model-selector.html)** - Settings (global)
5. **[05-results.html](05-results.html)** - Process/view results

### Legacy Pages (for reference):
- `02-schema-editor.html` - Now integrated into document type tabs
- `03-annotation.html` - Still useful for annotation flow
- `04-optimization.html` - Still useful for optimization progress

---

## New User Flow

### Creating a Document Type:
```
Dashboard
  ↓ Click "Create Document Type"
Document Types List
  ↓ Click "+ Create" or choose template
Document Type Detail (new type)
  ├── Tab 1: Define Schema ← Start here
  ├── Tab 2: Add Ground Truth (5 examples)
  ├── Tab 3: Optimize Pipeline (GEPA)
  └── Tab 4: View Analytics
```

### Managing Existing Type:
```
Dashboard
  ↓ Click "Manage" on Invoice card
Invoice Document Type Detail
  ├── Tab 1: Schema (15 fields)
  ├── Tab 2: Ground Truth (5 examples)
  ├── Tab 3: Pipeline (v3, 95.3% accuracy)
  └── Tab 4: Analytics (834 docs processed)
```

### Processing Documents:
```
Any page
  ↓ Click "Process"
Select Document Type (Invoice, Receipt, W2)
  ↓ Upload document
Results with Source Attribution
```

---

## Key Architectural Principles

### 1. Document Type = Container ✅
Each document type contains:
- **Schema** - Field definitions
- **Ground Truth** - Labeled examples
- **Pipeline** - GEPA-optimized extractor
- **Model Config** - Which LLM to use
- **Analytics** - Performance metrics

### 2. Independence ✅
- Invoice can use GPT-4o
- Receipt can use Claude 3.5
- W2 can use Gemini Pro
- Each has its own schema, examples, pipeline

### 3. Reusability ✅
- Templates provide pre-built schemas
- Users can clone/duplicate document types
- Export/import schemas

---

## Updated Navigation

### Top Nav (Global):
```
Dashboard | Document Types | Process | Settings
```

### Document Type Detail Tabs (Local):
```
Schema | Ground Truth | Pipeline & Optimization | Analytics
```

---

## File Organization

### Core Flow:
```
index.html
  ↓
document-types.html
  ↓
document-type-invoice.html (with 4 tabs)
  ├── Schema Tab
  ├── Ground Truth Tab
  ├── Pipeline Tab
  └── Analytics Tab
```

### Supporting Pages:
- `03-annotation.html` - Full-screen annotation interface
- `04-optimization.html` - Full-screen optimization dashboard
- `05-results.html` - Results viewer
- `01-model-selector.html` - Model switcher (can be invoked from any document type)

---

## Migration Notes

### If You Have the Old Prototype:
1. ✅ `index.html` - Updated navigation
2. ✅ `document-types.html` - NEW: List all types
3. ✅ `document-type-invoice.html` - NEW: Example detail page
4. ⚠️ `02-schema-editor.html` - Legacy: Now in document type tabs
5. ✅ `03-annotation.html` - Still valid: Full-screen annotation
6. ✅ `04-optimization.html` - Still valid: Full-screen optimization
7. ✅ `05-results.html` - Still valid: Results viewer

### What to Open First:
1. Open `index.html`
2. Click "Manage" on Invoice card
3. See tabbed interface in `document-type-invoice.html`
4. Explore Schema → Ground Truth → Pipeline → Analytics tabs

---

## Why This is Better

### Before (Wrong):
- User creates schema... but for which document type?
- User adds examples... but they're not linked to a type?
- Confusing navigation
- No clear ownership

### After (Correct):
- User creates "Invoice" document type
- All schema, examples, pipeline are **inside** Invoice
- Clear hierarchy and navigation
- Each type is self-contained

---

## Templates Feature

New in `document-types.html`:

Users can start from pre-built templates:
- 📄 Invoice
- 🧾 Receipt
- 📝 Contract
- 💼 Tax Forms
- 🪪 ID Cards
- 🏥 Medical Forms

Each template provides:
- Pre-defined schema with common fields
- Recommended field types and validation
- Extraction hints
- Users customize and add their own ground truth

---

## Next Steps

### For Testing:
1. Open `index.html`
2. Click "Manage" on Invoice → see tabbed interface
3. Click "Document Types" → see list with templates
4. Try creating new type from template

### For Development:
When building the real app:
- Document Type is a database model
- Each type has: `schema`, `examples`, `pipeline_version`, `model_config`
- API endpoints are scoped: `/api/document-types/{id}/schema`, etc.
- Frontend routes: `/document-types/:id/schema`, `/document-types/:id/pipeline`, etc.

---

## Summary

✅ **Schema is local to document type** - Each type has its own schema
✅ **Examples are local to document type** - Ground truth tied to specific type
✅ **Pipeline is local to document type** - Each type has independent pipeline
✅ **Model is local to document type** - Invoice can use GPT-4, Receipt can use Claude
✅ **Analytics are local to document type** - Track performance per type

This matches the requirements document (Section 5.1) and reflects how users actually think about document types!
