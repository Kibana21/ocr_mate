# OCR Mate Prototype - Quick Start Guide

## 🎯 What is This?

This is a **static HTML/CSS/JavaScript prototype** of the OCR Mate platform - a web application for intelligent structured document extraction using DSPy GEPA optimization.

**Purpose**: Visualize and test the UI/UX before building the full production application.

---

## 🚀 How to Use

### Option 1: Open Directly in Browser
1. Navigate to the `prototype` folder
2. Double-click `index.html`
3. Your default browser will open the prototype

### Option 2: Use VS Code Live Server
1. Install "Live Server" extension in VS Code
2. Right-click `index.html`
3. Select "Open with Live Server"
4. Prototype will open at `http://localhost:5500`

### Option 3: Simple HTTP Server
```bash
cd prototype
python3 -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## 📱 Pages Overview

### 1. **Dashboard** (`index.html`)
- Main landing page
- View all document types
- Quick stats and recent activity
- Navigate to other sections

### 2. **Model Selector** (`01-model-selector.html`)
- **Inspired by LangStruct**: Switch between LLM providers
- Compare OpenAI, Anthropic, Google, local models
- See estimated accuracy, speed, and cost
- One-click model switching

### 3. **Schema Editor** (`02-schema-editor.html`)
- Define document type (Invoice, Receipt, etc.)
- Add/edit extraction fields
- Configure field properties (type, validation, hints)
- Drag-and-drop field ordering (simulated)

### 4. **Annotation Interface** (`03-annotation.html`)
- Side-by-side document preview and form
- Label ground truth examples
- Click highlighted text to auto-fill fields
- Progress tracking

### 5. **Optimization Dashboard** (`04-optimization.html`)
- Real-time GEPA optimization progress
- Accuracy trend chart (visual)
- Field-level metrics breakdown
- Optimization log streaming

### 6. **Results with Source Attribution** (`05-results.html`)
- **Inspired by LangStruct**: Source highlighting
- Extracted data with confidence scores
- Interactive field-to-source mapping
- Hover over fields to highlight source
- Correction interface

---

## 🎨 User Flow

### Typical Journey:
```
Dashboard
    ↓
Create Document Type (Schema Editor)
    ↓
Upload & Label Examples (Annotation)
    ↓
Auto-Optimize Pipeline (Optimization Dashboard)
    ↓
Process Documents (Results)
    ↓
View with Source Attribution
```

### Quick Navigation:
- Use the top navigation bar to jump between sections
- All pages are interconnected with proper links

---

## 💡 Key Features Demonstrated

### ✅ Inspired by LangStruct
1. **Model Agnosticism** - Switch LLMs easily (01-model-selector.html)
2. **Source Attribution** - See where data came from (05-results.html)
3. **Zero Prompt Engineering** - Auto-optimization messaging
4. **Clean UX** - Simple, business-friendly interface

### ✅ OCR Mate Unique Features
1. **Document Focus** - Full OCR pipeline, not just text
2. **Visual Annotation** - Side-by-side document + form
3. **GEPA Optimization** - Real-time progress dashboard
4. **Business User Friendly** - No coding required

---

## 🔍 Interactive Elements

### Try These Interactions:

**On Dashboard (index.html):**
- Click document type cards to navigate
- View recent activity table

**On Model Selector (01-model-selector.html):**
- Click "Select" buttons to choose models
- View comparison table
- Try "Switch Model & Re-optimize" button

**On Schema Editor (02-schema-editor.html):**
- Click "Add Field" to see modal
- Edit/delete field buttons
- Save schema

**On Annotation (03-annotation.html):**
- Click highlighted text in invoice to auto-fill fields
- Try "Save & Next" button
- View progress bar

**On Optimization (04-optimization.html):**
- Watch progress bar animate
- View accuracy trend chart
- See field-level breakdown
- Read optimization log

**On Results (05-results.html):**
- **Hover over extracted fields** to see source highlighting
- View confidence scores
- Try export buttons
- Approve/reject actions

---

## 🎯 Testing Scenarios

### Scenario 1: New User Onboarding
1. Start at `index.html`
2. Click "Create Your First Document Type"
3. Goes to Schema Editor
4. Add fields
5. Proceed to Annotation
6. Label examples
7. Trigger optimization
8. View results

### Scenario 2: Model Switching (LangStruct-inspired)
1. Go to Settings (`01-model-selector.html`)
2. Compare different models
3. Select new model
4. Confirm re-optimization
5. Watch optimization progress

### Scenario 3: Document Processing
1. Upload document (simulated)
2. Run extraction
3. View results with source attribution
4. Hover over fields to see sources
5. Approve or correct

---

## 🎨 Design System

### Colors:
- **Primary**: Blue (#3b82f6) - Actions, links
- **Success**: Green (#10b981) - High confidence, completed
- **Warning**: Yellow (#f59e0b) - Medium confidence, needs review
- **Danger**: Red (#ef4444) - Low confidence, errors

### Typography:
- System fonts for performance
- Clear hierarchy (titles, subtitles, body)
- Accessible font sizes

### Layout:
- Responsive grid system
- Split views for document annotation/results
- Card-based design
- Clean, modern aesthetic

---

## 📊 What to Validate

Use this prototype to test:

### ✅ User Flow
- [ ] Is the navigation intuitive?
- [ ] Is the step-by-step process clear?
- [ ] Can users accomplish tasks without instructions?

### ✅ Visual Design
- [ ] Are confidence scores clear?
- [ ] Is source attribution understandable?
- [ ] Do colors convey meaning well?

### ✅ Information Architecture
- [ ] Is data well-organized?
- [ ] Are metrics easy to understand?
- [ ] Is the schema editor clear?

### ✅ Interactions
- [ ] Does hover highlighting work well?
- [ ] Are buttons well-labeled?
- [ ] Is feedback immediate?

---

## 🔄 Iteration Process

1. **Test with Users**:
   - Show to 5-10 potential users
   - Watch them use the prototype
   - Don't guide them - observe!

2. **Gather Feedback**:
   - What's confusing?
   - What's missing?
   - What works well?

3. **Iterate**:
   - Update HTML/CSS files
   - Refresh browser to see changes
   - No build process needed!

4. **Document Changes**:
   - Keep notes on what worked
   - Track requested features
   - Prioritize for MVP

---

## 🚧 Limitations (By Design)

This is a **static prototype**, so:
- ❌ No real backend
- ❌ No actual file uploads
- ❌ No real OCR processing
- ❌ No database
- ❌ Limited JavaScript (just for demos)

**This is intentional!** We want to:
- ✅ Focus on UX/UI validation
- ✅ Iterate quickly (just edit HTML)
- ✅ Get user feedback early
- ✅ Understand requirements before coding

---

## 📝 Next Steps After Validation

Once you've tested and iterated on this prototype:

1. **User Research**:
   - Interview 10-15 potential users
   - Validate pain points
   - Confirm willingness to pay

2. **High-Fidelity Design**:
   - Create polished mockups in Figma
   - Define complete design system
   - Create component library

3. **Technical POC**:
   - Build working DSPy + GEPA pipeline
   - Test with real invoice data
   - Measure accuracy improvements

4. **MVP Development**:
   - React frontend
   - FastAPI backend
   - Azure Document Intelligence integration
   - PostgreSQL database

---

## 🎨 Customization

Want to customize the prototype?

### Change Colors:
Edit `css/styles.css` - look for `:root` variables:
```css
:root {
  --primary-color: #3b82f6;  /* Change this! */
  --success-color: #10b981;
  /* etc. */
}
```

### Add New Fields:
Edit schema editor and annotation pages - copy existing field HTML

### Modify Layout:
All pages use the same CSS classes - change `css/styles.css`

### Add Mock Data:
Edit `js/app.js` - update `mockData` object

---

## 🆘 Troubleshooting

**Page looks broken?**
- Make sure CSS file is loading: check browser console
- Verify file paths are correct

**Interactions not working?**
- Check JavaScript console for errors
- Make sure `js/app.js` is loaded

**Want to test on mobile?**
- Use browser dev tools (Responsive Design Mode)
- Or use simple HTTP server and test on real device

---

## 📚 Learn More

### Inspiration:
- **LangStruct**: https://langstruct.dev/
- **DSPy**: https://dspy.ai/
- **GEPA**: https://dspy.ai/tutorials/gepa_facilitysupportanalyzer/

### Requirements:
- See `../REQUIREMENTS.md` for full product spec
- See `../COMPETITIVE_ANALYSIS.md` for market positioning

---

## ✨ Enjoy!

This prototype is meant to be:
- **Quick to modify** - just edit HTML/CSS
- **Easy to test** - no setup required
- **Informative** - validates UX before coding

**Have fun exploring the UI, and use this to gather feedback before building the real thing!**

---

**Questions or Feedback?**
Document your findings and iterate on the design. This is your playground to perfect the UX! 🚀
