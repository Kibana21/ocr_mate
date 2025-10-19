# OCR Mate - HTML/JS Prototype

## Purpose
This folder contains static HTML/JavaScript prototypes to visualize and test the UI/UX before building the full application.

## Structure
```
prototype/
├── index.html              # Main navigation/dashboard
├── 01-model-selector.html  # Model selection interface
├── 02-schema-editor.html   # Schema definition interface
├── 03-annotation.html      # Ground truth annotation interface
├── 04-optimization.html    # GEPA optimization dashboard
├── 05-results.html         # Extraction results with source attribution
├── css/
│   └── styles.css          # Shared styles
├── js/
│   └── app.js              # Shared JavaScript functionality
└── assets/
    └── sample-invoice.pdf  # Sample documents for testing

## How to Use
1. Open any HTML file directly in your browser
2. No server required - pure client-side HTML/CSS/JS
3. Click through the interfaces to understand the flow
4. Modify and iterate on designs quickly

## Pages Overview

### 1. Model Selector (01-model-selector.html)
- Switch between LLM providers (OpenAI, Claude, Gemini)
- Compare model performance and costs
- One-click model switching

### 2. Schema Editor (02-schema-editor.html)
- Define document type
- Add/edit/remove fields
- Configure field properties and validation rules
- Drag-and-drop field reordering

### 3. Annotation Interface (03-annotation.html)
- Side-by-side document preview and extraction form
- OCR text display
- Ground truth labeling
- Progress tracking

### 4. Optimization Dashboard (04-optimization.html)
- Real-time GEPA optimization progress
- Accuracy trend charts
- Field-level metrics
- Iteration tracking

### 5. Results with Source Attribution (05-results.html)
- Extracted data display
- Confidence scores
- Source highlighting on document
- Interactive field-to-source mapping
- Correction interface

## Design Principles
- Clean, modern interface
- Responsive layout
- Accessibility-friendly
- Inspired by LangStruct's simplicity
- Focus on business user experience

## Technology Stack (Prototype)
- HTML5
- CSS3 (Flexbox/Grid)
- Vanilla JavaScript (no frameworks for simplicity)
- Font: System fonts or Google Fonts
- Icons: Unicode or simple SVG

## Next Steps
After validating the UI:
1. User testing with 5-10 potential users
2. Iterate based on feedback
3. Create high-fidelity designs
4. Build production app with React + FastAPI
