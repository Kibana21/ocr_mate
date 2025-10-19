# Context-Aware Navigation Fix

## Issue Fixed
When clicking "Edit" on a ground truth example in the Invoice document type, it was navigating to the standalone annotation page without context about which document type it belonged to.

## Solution
Made the annotation interface **context-aware** using URL parameters and updated navigation.

---

## How It Works Now

### 1. From Document Type Detail Page

When you click "Edit" or "+ Add Example" in `document-type-invoice.html`:

```javascript
// Ground Truth Tab - Add Example button
function addExample() {
  // Passes document_type parameter in URL
  window.location.href = '03-annotation.html?document_type=invoice';
}

// Ground Truth Tab - Edit button
function editExample(filename) {
  // Shows alert explaining what would happen in real app
  alert(`Edit annotation for ${filename} (Invoice document type)

In the real app, this would:
1. Load the document
2. Pre-fill existing labeled values
3. Allow you to correct/update labels
4. Save back to Invoice ground truth`);
}
```

### 2. Annotation Page Reads Context

The `03-annotation.html` page now:

```javascript
// Read document type from URL
const urlParams = new URLSearchParams(window.location.search);
const documentType = urlParams.get('document_type') || 'unknown';

// Update UI to show context
window.addEventListener('DOMContentLoaded', () => {
  if (documentType !== 'unknown') {
    const typeName = documentType.charAt(0).toUpperCase() + documentType.slice(1);
    document.getElementById('breadcrumb-context').textContent = `Annotate ${typeName} Example`;
  }
});
```

### 3. Return Navigation

Added breadcrumb and "Back to Invoice" button:

```javascript
function returnToDocType() {
  if (documentType === 'invoice') {
    window.location.href = 'document-type-invoice.html?tab=examples';
  } else {
    window.location.href = 'document-types.html';
  }
}
```

---

## Updated UI Elements

### Annotation Page Now Shows:

1. **Breadcrumb**:
   ```
   Dashboard / Document Types / Invoice / Ground Truth Examples
   ```

2. **Page Title**:
   ```
   Label Example 2 of 5 (Invoice)
   ```

3. **Description**:
   ```
   Provide correct values for each field to train the Invoice extraction pipeline
   ```

4. **Navigation**:
   ```
   [← Back to Invoice] [Skip] [Save & Next →]
   ```

---

## User Flow Example

### Flow 1: Add New Example
```
1. Dashboard
   ↓ Click "Manage" on Invoice
2. document-type-invoice.html (Ground Truth tab)
   ↓ Click "+ Add Example"
3. 03-annotation.html?document_type=invoice
   ↓ Label fields
   ↓ Click "Save & Next"
4. Shows: "Ground truth saved for Invoice document type!"
   ↓ Click "← Back to Invoice"
5. Returns to: document-type-invoice.html?tab=examples
```

### Flow 2: Edit Existing Example
```
1. document-type-invoice.html (Ground Truth tab)
   ↓ Click "Edit" on invoice_example_001.pdf
2. Alert shows what would happen:
   - "Edit annotation for invoice_example_001.pdf (Invoice document type)"
   - Explains: Load doc, pre-fill values, allow corrections, save to Invoice
3. (In real app: would navigate to annotation page with pre-loaded data)
```

---

## URL Parameter Pattern

### Pattern:
```
03-annotation.html?document_type={type_id}
```

### Examples:
- `03-annotation.html?document_type=invoice`
- `03-annotation.html?document_type=receipt`
- `03-annotation.html?document_type=w2_form`

### In Real App:
You might use document type ID instead:
```
03-annotation.html?document_type_id=dt_abc123&example_id=ex_xyz789
```

This would:
1. Fetch schema for `dt_abc123`
2. Load existing labels for `ex_xyz789` (if editing)
3. Render annotation form with correct fields
4. Save back to the correct document type

---

## Benefits

✅ **Context Clarity**: User always knows which document type they're working on
✅ **Proper Navigation**: Can return to the correct document type detail page
✅ **Scoped Data**: Ground truth is saved to the correct document type
✅ **Breadcrumbs**: Clear navigation path
✅ **Better UX**: No confusion about where labels are being saved

---

## What Changed in Files

### `document-type-invoice.html`
- ✅ "+ Add Example" button calls `addExample()` with confirm dialog
- ✅ "Edit" buttons call `editExample(filename)` with explanatory alert
- ✅ "Delete" buttons call `deleteExample(filename)` with confirmation

### `03-annotation.html`
- ✅ Added breadcrumb navigation
- ✅ Updated page title to show "(Invoice)"
- ✅ Added "← Back to Invoice" button
- ✅ JavaScript reads `document_type` from URL
- ✅ `returnToDocType()` navigates back correctly
- ✅ `saveAndNext()` shows which type is being saved

---

## For Real Implementation

When building the actual app, you would:

### 1. API Routes
```
GET  /api/document-types/{id}/examples          # List examples
POST /api/document-types/{id}/examples          # Create example
GET  /api/document-types/{id}/examples/{ex_id}  # Get example
PUT  /api/document-types/{id}/examples/{ex_id}  # Update example
DEL  /api/document-types/{id}/examples/{ex_id}  # Delete example
```

### 2. Frontend Routes
```
/document-types/:typeId/examples/new            # Add new example
/document-types/:typeId/examples/:exampleId     # Edit existing
```

### 3. React Example
```jsx
// In DocumentTypeDetail.tsx
function GroundTruthTab({ documentTypeId }) {
  const navigate = useNavigate();

  const handleAddExample = () => {
    navigate(`/document-types/${documentTypeId}/examples/new`);
  };

  const handleEditExample = (exampleId) => {
    navigate(`/document-types/${documentTypeId}/examples/${exampleId}`);
  };
}

// In AnnotationPage.tsx
function AnnotationPage() {
  const { typeId, exampleId } = useParams();
  const documentType = useFetchDocumentType(typeId);
  const example = exampleId ? useFetchExample(exampleId) : null;

  // Pre-fill form if editing existing example
  // Save back to /api/document-types/{typeId}/examples
}
```

---

## Testing

### Test Flow:
1. Open `document-type-invoice.html`
2. Click on "Ground Truth" tab
3. Click "+ Add Example"
4. Confirm dialog → navigates to `03-annotation.html?document_type=invoice`
5. Notice breadcrumb shows "Invoice"
6. Notice title shows "(Invoice)"
7. Click "← Back to Invoice" → returns to Invoice detail page
8. Click "Edit" on any example → shows explanatory alert

---

## Summary

The annotation interface is now **scoped to the document type** it belongs to. Users have clear context about which document type they're labeling, and navigation properly returns them to the correct place.

This matches the document-centric architecture where everything (schema, examples, pipeline) is local to each document type.
