# OCR Mate - HTML/CSS/JS Prototype

## Purpose
This folder contains a fully functional static HTML/CSS/JavaScript prototype that demonstrates the complete user journey and UI/UX for OCR Mate. The prototype validates the **document-centric architecture** and serves as the specification for frontend implementation.

## Quick Start
1. Open `index.html` in your browser (no server required)
2. Navigate to "Document Types" → Click "Invoice"
3. Explore the 4 tabs: Schema, Ground Truth, Pipeline, Analytics
4. Try the "Process" page to see document upload and processing queue
5. Click around to understand the navigation flow

## Architecture

### Document-Centric Design
Each document type (Invoice, Receipt, Contract, etc.) is a **self-contained unit** with its own:
- Schema definition (fields to extract)
- Ground truth examples (labeled documents)
- Optimization pipeline (GEPA-powered)
- Performance analytics (accuracy, processing history)

This ensures users never lose context about which document type they're working with.

### Navigation Structure
```
Dashboard | Document Types | Process | Settings
                 ↓
        [Click Invoice Card]
                 ↓
      Document Type Detail Page
      ├── Tab: Schema
      ├── Tab: Ground Truth Examples
      ├── Tab: Pipeline & Optimization
      └── Tab: Performance Analytics
```

## Files

### Core Pages
| File | Purpose | Features |
|------|---------|----------|
| `index.html` | Dashboard | Overview metrics, recent activity, quick actions |
| `document-types.html` | All document types | Grid view, templates, create new button |
| `document-type-invoice.html` | Invoice detail | 4 tabs (Schema, Ground Truth, Pipeline, Analytics) |
| `process-documents.html` | Processing hub | Upload, live queue, recent completions (global) |
| `01-model-selector.html` | Settings | Model configuration, account, API keys |

### Context-Aware Pages
| File | Purpose | Context Handling |
|------|---------|------------------|
| `03-annotation.html` | Ground truth annotation | URL param: `?document_type=invoice` |
| `04-optimization.html` | GEPA optimization progress | Shows document type badge, breadcrumbs |
| `05-results.html` | Extraction results | Source attribution, back to analytics tab |

### Deprecated
| File | Status |
|------|--------|
| `02-schema-editor.html` | Redirects to `document-types.html` (schema now in document type tabs) |

## Key Features Demonstrated

### 1. Context-Aware Navigation
- **Breadcrumbs** on all pages: `Dashboard / Document Types / Invoice / Ground Truth`
- **Document type badges** in page titles
- **"Back to [Type]" buttons** that return to correct tab
- **URL parameters** maintain state: `?document_type=invoice&tab=schema`

### 2. Live Processing Visualization
- Animated **spinners** for processing documents
- **Progress bars** (0-100%)
- Real-time counters: "3 processing, 5 queued"
- Processing stage: "Running OCR...", "Extracting fields..."
- Color-coded status badges

### 3. Source Attribution (LangStruct-inspired)
- **Split-view** layout: source document | extracted data
- **Hover over field** → highlight source in document (yellow background)
- **Click field** → jump to source location
- Shows exact text span and line number

### 4. Drag & Drop Upload
- Visual upload zone with drag-over state
- Multi-file selection
- File size display and individual removal
- Document type selection with real-time stats

### 5. Processing History
- Table of all processed documents per document type
- Filtering, search, date range
- Live updates (WebSocket simulation)
- Export to CSV

### 6. Design System
- **CSS Variables** for theming
- Reusable components (buttons, badges, cards, tables)
- Responsive grid layouts
- Color-coded by status and type

## Design System

### CSS Variables (`css/styles.css`)
```css
--primary-color: #2563eb      /* Blue */
--success-color: #059669      /* Green */
--warning-color: #d97706      /* Orange */
--danger-color: #dc2626       /* Red */

--spacing-xs: 0.25rem         /* 4px */
--spacing-sm: 0.5rem          /* 8px */
--spacing-md: 1rem            /* 16px */
--spacing-lg: 1.5rem          /* 24px */
--spacing-xl: 2rem            /* 32px */
```

### Component Classes
- `.btn` - Buttons (primary, secondary, success, danger, warning)
- `.badge` - Status badges with color variants
- `.card` - Container with header and body
- `.table` - Styled data tables
- `.spinner` - Animated loading indicator
- `.tab`, `.tab-content` - Tab navigation system

## Interactive Features (JavaScript)

### Tab Switching with URL State
```javascript
function showTab(tabName) {
  // Update content visibility
  document.querySelectorAll('.tab-content').forEach(content => {
    content.style.display = 'none';
  });
  document.getElementById('content-' + tabName).style.display = 'block';

  // Update URL parameter for deep linking
  const url = new URL(window.location);
  url.searchParams.set('tab', tabName);
  window.history.pushState({}, '', url);

  // Update active styling
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });
  document.getElementById('tab-' + tabName).classList.add('active');
}
```

### Context Awareness via URL Parameters
```javascript
const urlParams = new URLSearchParams(window.location.search);
const documentType = urlParams.get('document_type') || 'unknown';

function returnToDocType() {
  if (documentType === 'invoice') {
    window.location.href = 'document-type-invoice.html?tab=examples';
  }
}
```

### Drag & Drop File Upload
```javascript
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  const files = Array.from(e.dataTransfer.files);
  addFiles(files);
});
```

## User Flows

### Creating a Document Type
1. Dashboard → "Document Types"
2. Click template (e.g., "Invoice") or "Create New"
3. Opens `document-type-invoice.html` with Schema tab active
4. Define fields (name, type, validation rules, hints)
5. Switch to "Ground Truth Examples" tab
6. Upload sample documents and annotate
7. Switch to "Pipeline & Optimization" tab
8. Click "Optimize Pipeline" → GEPA runs
9. Switch to "Performance Analytics" tab
10. View metrics and processing history

### Processing Documents
1. Click "Process" in top navigation
2. Select document type from dropdown
3. Drag & drop files or click to browse
4. Review selected files list
5. Configure processing options (checkboxes)
6. Click "Process Documents"
7. Watch live processing queue update in real-time
8. Completed documents appear in "Recent Completions"
9. Click "View" to see extraction results

### Viewing Results
1. From processing history, click "View"
2. See split-view: source document | extracted data
3. Hover over field → source highlights in yellow
4. Click field → jump to source location
5. Review confidence scores per field
6. Approve, correct errors, or reject

## Next Steps: From Prototype to Production

### Frontend Migration
1. Port HTML/CSS to **React/Vue** components
2. Replace vanilla JS with **state management** (Redux/Pinia)
3. Integrate with **REST API** endpoints
4. Add **WebSocket** for real-time updates
5. Implement **authentication** (Auth0)
6. Add error boundaries and loading states

### Backend Integration Points
- `GET /api/v1/document-types` - Load document types
- `POST /api/v1/document-types` - Create new type
- `PUT /api/v1/document-types/:id/schema` - Update schema
- `POST /api/v1/ground-truth` - Upload examples
- `POST /api/v1/pipelines/:id/optimize` - Trigger GEPA
- `WS /api/v1/pipeline/:id/optimization-status` - Live updates
- `POST /api/v1/extract` - Process document
- `POST /api/v1/extract/batch` - Batch processing
- `WS /api/v1/processing-queue` - Live queue updates
- `GET /api/v1/results/:id` - Get results

### Prototype Value
- ✅ Visual specification for frontend developers
- ✅ UX reference for user flows
- ✅ Design system documentation
- ✅ Test cases for E2E testing (Playwright/Cypress)
- ✅ Demo for user testing and stakeholder feedback

## Technology Stack (Prototype)
- **HTML5** - Semantic markup
- **CSS3** - Flexbox/Grid, CSS Variables
- **Vanilla JavaScript** - No frameworks (simplicity)
- **No build tools** - Direct browser execution
- **No backend** - Static files only

## Design Principles
- **Clean, modern interface** - Minimal clutter
- **Responsive layout** - Works on desktop/tablet
- **Accessibility-friendly** - ARIA labels, keyboard navigation
- **Inspired by LangStruct** - Simplicity, source attribution
- **Business user focused** - Non-technical language, visual feedback

## Documentation

All implementation details, architecture decisions, and feature specifications are documented in:

**`/REQUIREMENTS.md`** - Comprehensive Product Requirements Document including:
- Section 5.1: Navigation Structure (document-centric architecture)
- Section 5.4: Prototype Implementation (this prototype)
- Section 3.3.2: Batch Processing & Global Processing Hub
- Complete API specifications and technical architecture

## Questions?

Refer to `/REQUIREMENTS.md` for detailed specifications, or explore the prototype by opening `index.html` in your browser.
