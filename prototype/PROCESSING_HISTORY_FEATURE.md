# Processing History Feature

## Issue Fixed
The Performance Analytics tab needed better styling and was missing a critical feature: **real-time visibility into document processing**.

## Solution
Added a comprehensive "Processing History" section that shows all documents being processed through the Invoice pipeline, including live processing status.

---

## New Features in Performance Analytics Tab

### 1. Performance Metrics (Improved Styling)
- ✅ Proper card layout with header
- ✅ Clear metrics grid (4 KPI cards)
- ✅ Green up/down indicators
- ✅ Time-based context (this week, this month)

### 2. Processing History (NEW!)
Real-time view of all documents being processed for this document type.

#### Features:
- **Live Processing Queue** - Shows documents currently being processed
- **Filter Bar** - Status, date range, search by filename
- **Detailed Table** - Full history with all metadata
- **Pagination** - Navigate through 834 processed documents
- **Export** - Download CSV of processing history

#### Table Columns:
1. **Document** - Filename with live spinner for processing docs
2. **Status** - Completed, Processing, Failed, Review Required
3. **Accuracy** - Overall extraction accuracy %
4. **Confidence** - Model confidence score
5. **Processing Time** - How long extraction took
6. **Processed By** - API User, Web Upload, Batch Job
7. **Timestamp** - When processed
8. **Actions** - View results, Review, Retry

### 3. Field-Level Analytics (NEW!)
Track performance per field with trends.

#### Columns:
- Field name
- Average accuracy
- Average confidence
- Manual correction rate
- Trend (Improving, Stable, Needs Attention)

---

## Live Processing Indicator

```
┌────────────────────────────────────────────────┐
│ ● Live: 3 documents in queue, 2 processing now│
└────────────────────────────────────────────────┘
```

- **Pulsing blue dot** - Indicates system is actively processing
- **Queue count** - How many docs waiting
- **Processing count** - How many currently running

---

## Use Cases

### Use Case 1: Monitor API Usage
**Scenario**: You have API clients hitting your Invoice endpoint

**What you see**:
```
Processing History Table:
- invoice_live_001.pdf [Processing] - API User - Just now
- invoice_live_002.pdf [Processing] - Web Upload - 5 sec ago
- invoice_2024_089.pdf [Completed] - API User - 2 mins ago
```

**Actions**:
- See which documents are being processed right now
- Filter by "Processed By" to see API vs Web usage
- Export CSV for billing/usage analysis

### Use Case 2: Identify Low-Confidence Extractions
**Scenario**: You want to improve pipeline accuracy

**What you see**:
```
Filter: Status = "Review Required"
- invoice_2024_088.pdf [76.4% accuracy] - Needs review
```

**Actions**:
- Click "Review" to see what went wrong
- Add to ground truth if it's a common pattern
- Re-optimize pipeline with new examples

### Use Case 3: Debug Failures
**Scenario**: Some documents are failing to process

**What you see**:
```
- invoice_2024_085.pdf [Failed] - 0.5s - 20 mins ago [Retry]
```

**Actions**:
- Click "Retry" to reprocess
- View error logs (in real app)
- Fix schema or OCR issues

### Use Case 4: Track Performance Over Time
**Scenario**: You want to see if accuracy is improving

**What you see**:
```
Field-Level Analytics:
- Invoice Number: 98.2% (↑ Improving)
- Total Amount: 89.3% (↓ Needs Attention)
```

**Actions**:
- Focus ground truth examples on "Total Amount"
- Re-optimize pipeline
- Monitor trend after changes

---

## Real-Time Updates (How It Would Work)

### Prototype (Current):
- Static data showing what the interface looks like
- Spinner animations to simulate live processing
- Blue pulsing dot for visual effect

### Real App (Future):
```javascript
// WebSocket connection for real-time updates
const ws = new WebSocket('ws://api.ocrmate.ai/document-types/invoice/processing');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  if (update.type === 'processing_started') {
    // Add new row with spinner
    addProcessingRow(update.document);
  } else if (update.type === 'processing_completed') {
    // Update row with results
    updateRow(update.document_id, {
      status: 'completed',
      accuracy: update.accuracy,
      confidence: update.confidence,
      processingTime: update.time
    });
  } else if (update.type === 'queue_status') {
    // Update live indicator
    updateQueueIndicator(update.queue_count, update.processing_count);
  }
};
```

---

## Filter Options

### Status Filter:
- All Statuses
- Completed (97.2% of docs)
- Processing (live docs)
- Failed (retry required)
- Review Required (low confidence)

### Time Range Filter:
- Last 24 hours
- Last 7 days
- Last 30 days
- All time

### Search:
- Search by filename
- In real app: also search by metadata, user, etc.

---

## Export Functionality

### CSV Export Includes:
```csv
Document,Status,Accuracy,Confidence,Processing_Time,Processed_By,Timestamp
invoice_2024_089.pdf,Completed,98.2%,97.1%,3.1s,API User,2024-10-19 14:32:15
invoice_2024_088.pdf,Review Required,76.4%,68.2%,3.4s,Web Upload,2024-10-19 14:27:42
...
```

### Use Cases for Export:
- **Billing**: Track API usage by client
- **Analytics**: Analyze patterns in external tools
- **Compliance**: Audit trail for processed documents
- **Reporting**: Monthly reports for stakeholders

---

## API Endpoints (Real Implementation)

### Get Processing History:
```
GET /api/document-types/{type_id}/processing-history
Query params:
  - status: completed|processing|failed|review_required
  - date_from: ISO timestamp
  - date_to: ISO timestamp
  - search: filename search
  - page: pagination
  - limit: results per page

Response:
{
  "total": 834,
  "page": 1,
  "limit": 10,
  "data": [
    {
      "id": "proc_abc123",
      "document_id": "doc_xyz789",
      "filename": "invoice_2024_089.pdf",
      "status": "completed",
      "accuracy": 98.2,
      "confidence": 97.1,
      "processing_time_ms": 3100,
      "processed_by": "api_user_123",
      "timestamp": "2024-10-19T14:32:15Z",
      "result_url": "/api/results/res_def456"
    }
  ]
}
```

### WebSocket for Live Updates:
```
WS /ws/document-types/{type_id}/live

Messages:
{
  "type": "processing_started",
  "document_id": "doc_xyz789",
  "filename": "invoice_live_001.pdf",
  "processed_by": "api_user_123"
}

{
  "type": "processing_completed",
  "document_id": "doc_xyz789",
  "status": "completed",
  "accuracy": 98.2,
  "confidence": 97.1,
  "processing_time_ms": 3100
}

{
  "type": "queue_status",
  "queue_count": 3,
  "processing_count": 2
}
```

### Export History:
```
GET /api/document-types/{type_id}/processing-history/export?format=csv
```

---

## Database Schema (Real Implementation)

### processing_jobs table:
```sql
CREATE TABLE processing_jobs (
  id UUID PRIMARY KEY,
  document_type_id UUID REFERENCES document_types(id),
  document_id UUID REFERENCES documents(id),
  filename VARCHAR(255),
  status VARCHAR(50), -- processing, completed, failed, review_required
  accuracy DECIMAL(5,2),
  confidence DECIMAL(5,2),
  processing_time_ms INTEGER,
  processed_by VARCHAR(100), -- user_id or api_key or batch_job_id
  source VARCHAR(50), -- web_upload, api, batch_job
  result_id UUID REFERENCES extraction_results(id),
  error_message TEXT,
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  INDEX idx_document_type_status (document_type_id, status),
  INDEX idx_created_at (created_at DESC)
);
```

---

## Benefits

### For Admins:
✅ **Monitor system health** - See if processing is working
✅ **Identify issues** - Find failed or low-confidence extractions
✅ **Track usage** - See who's using the system
✅ **Improve accuracy** - Find patterns to add to ground truth

### For Users:
✅ **Visibility** - Know status of uploaded documents
✅ **Confidence** - See what's being processed live
✅ **Troubleshooting** - Retry failed documents
✅ **Analytics** - Track performance over time

### For Developers:
✅ **Debugging** - See real-time processing
✅ **Performance** - Monitor processing times
✅ **Testing** - Verify pipeline changes
✅ **Metrics** - Export data for analysis

---

## Visual Indicators

### Status Badges:
- 🔵 **Processing** - Blue badge, spinner icon
- ✅ **Completed** - Green badge
- ⚠️ **Review Required** - Yellow badge
- ❌ **Failed** - Red badge

### Trends:
- ↑ **Improving** - Green text
- → **Stable** - Gray text
- ↓ **Needs Attention** - Yellow/orange text

### Live Indicator:
- 🔵 **Pulsing dot** - Active processing
- **Queue count** - Waiting documents
- **Processing count** - Currently running

---

## Summary

The Performance Analytics tab now provides:

1. ✅ **Performance Metrics** - High-level KPIs
2. ✅ **Processing History** - Real-time table of all processed docs
3. ✅ **Live Queue Indicator** - See what's processing right now
4. ✅ **Filters & Search** - Find specific documents
5. ✅ **Export** - Download CSV for analysis
6. ✅ **Field-Level Analytics** - Track performance per field

This gives admins complete visibility into document processing while they manage the pipeline, even as API clients and web users continue to submit documents for processing.
