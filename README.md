# Dynamic ETL Pipeline System

## Overview
A dynamic ETL pipeline system that ingests files containing mixed data formats (HTML, JSON, CSV) and provides:
- Automatic schema generation and evolution
- Database-agnostic data storage
- Natural language query interface using local LLM (Ollama + Qwen)
- FastAPI backend with comprehensive API endpoints
- Streamlit frontend for easy interaction

## Architecture

### Backend (FastAPI)
- **File Parser**: Extracts text from .txt, .pdf, .md files
- **Data Extractor**: Identifies and extracts HTML, JSON, CSV fragments using hybrid SLM + heuristic approach
- **Data Cleaner**: Canonicalizes fields, deduplicates records
- **Schema Manager**: Generates and updates database-agnostic schemas
- **Query Executor**: Executes both natural language and direct MongoDB queries

### Frontend (Streamlit)
Single-page application with:
- File upload interface
- Schema viewer
- Query interface (NL and DB queries)
- Upload and query history

### Database (MongoDB)
- Dynamic collections based on extracted data
- Schema versioning and evolution
- Query and upload audit trails

### LLM Integration (Ollama)
- **SLM**: qwen2.5:0.5b for data type detection
- **LLM**: qwen2.5:0.5b for NL to MongoDB query translation
- Fully local, no external API dependencies

## API Endpoints

### POST /api/upload
Upload and process a file through ETL pipeline.

**Request:**
- `source_id` (form field): Unique identifier for data source
- `file` (multipart): File to upload (.txt, .pdf, .md)

**Response:**
```json
{
  "source_id": "string",
  "status": "success",
  "parsed_summary": {
    "fragments": [...],
    "total_fragments": 0,
    "total_records": 0,
    "data_types": ["html", "json", "csv"]
  },
  "schema": {...}
}
```

### GET /api/schema?source_id=
Fetch schema for a source.

**Response:**
```json
{
  "source_id": "string",
  "schema": {
    "version": 1,
    "collections": {...},
    "data_types_present": []
  }
}
```

### POST /api/query
Execute a query (NL or DB).

**Request:**
```json
{
  "source_id": "string",
  "query_type": "NL" | "DB",
  "query_text": "string"
}
```

**Response:**
```json
{
  "source_id": "string",
  "input_query_type": "NL",
  "db_query_translated": "...",
  "execution_result": [...],
  "error": null
}
```

### GET /api/records?source_id=&query_id=
Fetch records for a source.

### GET /api/history/uploads?source_id=
Get upload history.

### GET /api/history/queries?source_id=
Get query history.

## Setup & Running

### Prerequisites
- Python 3.11+
- MongoDB running on localhost:27017
- Ollama installed and running

### Installation

1. Install dependencies:
```bash
cd /app/backend
pip install -r requirements.txt
```

2. Install Ollama and pull model:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5:0.5b
```

3. Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart etl_backend streamlit
```

### Access
- **Backend API**: http://localhost:8001/api
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8001/docs

## Testing

### Create Test Files

**test_mixed.txt** (contains JSON and CSV):
```
{"product_id": 1, "name": "Widget", "price": 29.99}
{"product_id": 2, "name": "Gadget", "price": 49.99}

id,name,category
101,Item A,Electronics
102,Item B,Books
```

**test_html.txt** (contains HTML table):
```html
<table>
  <thead><tr><th>Name</th><th>Age</th></tr></thead>
  <tbody>
    <tr><td>Alice</td><td>30</td></tr>
    <tr><td>Bob</td><td>25</td></tr>
  </tbody>
</table>
```

### Example Workflow

1. Upload file via Streamlit UI or API
2. View generated schema
3. Query data using natural language:
   - "Show me all products"
   - "Find items with price greater than 30"
   - "List all records"

## Design Decisions

### Hybrid Parsing Approach
**Justification**: While SLM can detect data types, heuristic parsers (BeautifulSoup, csv module, json parser) are more reliable for actual extraction. We use:
- **SLM (qwen2.5:0.5b)**: Initial detection and boundary identification
- **Heuristic Parsers**: Actual data extraction and validation

This provides:
- Better accuracy for well-formed data
- Graceful handling of malformed data
- Performance optimization (SLM only for detection, not extraction)

### Database-Agnostic Schema
Schema design supports:
- Dynamic field addition
- Type evolution (fields can change types across uploads)
- Version tracking
- Multiple data collections per source

### Local LLM for Query Translation
- **Privacy**: All data processing is local
- **Cost**: No API costs
- **Flexibility**: Can swap models easily
- **Trade-off**: Accuracy may be lower than GPT-4, but sufficient for common queries

## Logging

All operations are logged:
- Upload events with fragment counts
- Schema generation and updates
- Query executions with results
- Errors and warnings

Logs available at:
- Backend: `/var/log/supervisor/etl_backend.*.log`
- Streamlit: `/var/log/supervisor/streamlit.*.log`
- Ollama: `/var/log/ollama.log`

## Limitations

1. **File Size**: Large files (>50MB) may timeout during processing
2. **LLM Accuracy**: Local small models may not handle complex NL queries perfectly
3. **Concurrency**: Single-threaded processing (can be improved with Celery)
4. **Storage**: MongoDB on single instance (production would need replica sets)

## Future Enhancements

- Add support for more file formats (Excel, XML, Parquet)
- Implement streaming for large files
- Add data validation and quality checks
- Support for relationships between collections
- Query result caching
- Real-time schema evolution visualization
