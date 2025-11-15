# ETL Pipeline System - Usage Guide

## Quick Start

### 1. Access the Application
- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8002/docs
- **API Endpoint**: http://localhost:8002/api

### 2. Upload Your First File

#### Via Streamlit UI:
1. Open http://localhost:8501
2. Navigate to "Upload & Process" page
3. Enter a Source ID (e.g., "my_project")
4. Upload a .txt, .pdf, or .md file
5. Click "Process File"
6. View the extracted fragments and generated schema

#### Via API:
```bash
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=my_project" \
  -F "file=@/path/to/your/file.txt"
```

## Example Workflow

### Step 1: Prepare Test Data

Create a file `sales_data.txt` with mixed data types:

```
Sales Report Q1 2025
====================

Product Sales (JSON):
{"product": "Laptop", "sales": 150, "revenue": 149985.0}
{"product": "Mouse", "sales": 300, "revenue": 8997.0}
{"product": "Keyboard", "sales": 200, "revenue": 15998.0}

Customer List (CSV):
customer_id,name,country,total_purchases
C001,Alice Johnson,USA,2500
C002,Bob Smith,Canada,1800
C003,Carol Davis,UK,3200

Store Performance (HTML):
<table>
  <tr><th>Store</th><th>Location</th><th>Revenue</th></tr>
  <tr><td>Store A</td><td>New York</td><td>$250,000</td></tr>
  <tr><td>Store B</td><td>LA</td><td>$180,000</td></tr>
</table>
```

### Step 2: Upload File

```bash
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=sales_q1" \
  -F "file=@sales_data.txt"
```

**Response shows:**
- Fragments detected: 3 (JSON, CSV, HTML)
- Records extracted: 8
- Schema generated with field types

### Step 3: View Schema

```bash
curl "http://localhost:8002/api/schema?source_id=sales_q1"
```

**Response shows:**
- Version: 1
- Collections: json_data, csv_data, html_data
- Field definitions with types and samples

### Step 4: Query Data

#### Option A: Natural Language Query
```bash
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "sales_q1",
    "query_type": "NL",
    "query_text": "Show me products with sales greater than 200"
  }'
```

#### Option B: Direct MongoDB Query
```bash
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "sales_q1",
    "query_type": "DB",
    "query_text": "{\"operation\": \"find\", \"filter\": {\"sales\": {\"$gt\": 200}}, \"projection\": {\"_id\": 0}}"
  }'
```

### Step 5: Fetch All Records

```bash
curl "http://localhost:8002/api/records?source_id=sales_q1"
```

### Step 6: View History

#### Upload History:
```bash
curl "http://localhost:8002/api/history/uploads?source_id=sales_q1"
```

#### Query History:
```bash
curl "http://localhost:8002/api/history/queries?source_id=sales_q1"
```

## Data Type Detection

The system automatically detects and extracts:

### JSON
- Single-line JSON objects: `{"key": "value"}`
- Multi-line JSON objects and arrays
- Nested structures
- Handles malformed JSON with basic fixes

### CSV
- Comma-separated values
- Alternative delimiters: semicolon, tab, pipe
- With or without headers
- Multi-column data

### HTML
- HTML tables (`<table>` tags)
- Extracts structured data from table rows
- Supports thead/tbody structure
- Converts to dictionary format

## Schema Evolution

When uploading multiple files to the same `source_id`:

1. **First Upload**: Creates schema v1
2. **Second Upload**: Merges with existing schema → v2
   - New fields are added
   - Existing fields are validated
   - Type conflicts marked as "mixed"
3. **Subsequent Uploads**: Continue incrementing version

Example:
```bash
# Upload 1: Products with id, name, price
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=products" \
  -F "file=@products_v1.txt"
# Schema v1 created

# Upload 2: Products with id, name, price, category
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=products" \
  -F "file=@products_v2.txt"
# Schema v2: adds "category" field

# Upload 3: Products with all fields + rating
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=products" \
  -F "file=@products_v3.txt"
# Schema v3: adds "rating" field
```

## Query Examples

### Natural Language Queries

```bash
# Find all records
"Show me all products"

# Filter by value
"Find customers from USA"

# Numeric comparison
"List products with price greater than 100"

# Count records
"How many customers do we have?"

# Aggregation
"What is the total revenue?"
```

### MongoDB Direct Queries

#### Find All
```json
{
  "operation": "find",
  "filter": {},
  "projection": {"_id": 0}
}
```

#### Filter by Field
```json
{
  "operation": "find",
  "filter": {"category": "Electronics"},
  "projection": {"_id": 0}
}
```

#### Numeric Comparison
```json
{
  "operation": "find",
  "filter": {"price": {"$gt": 100}},
  "projection": {"_id": 0}
}
```

#### Aggregation
```json
{
  "operation": "aggregate",
  "pipeline": [
    {"$group": {"_id": null, "total": {"$sum": "$revenue"}}},
    {"$project": {"_id": 0, "total_revenue": "$total"}}
  ]
}
```

## Using Streamlit UI

### Navigation

1. **Upload & Process**: Upload files and view processing results
2. **View Schema**: Browse schema details and field definitions
3. **Query Data**: Execute NL or DB queries and view results
4. **History**: View upload and query logs

### Upload Page Features

- File upload (drag-and-drop supported)
- Source ID management
- Real-time processing status
- Fragment preview with samples
- Schema generation summary

### Query Page Features

- Toggle between NL and DB query modes
- Query editor with syntax examples
- Result viewer with JSON formatting
- Translated query display (for NL queries)

### Schema Page Features

- Schema metadata (version, collections, data types)
- Field browser with type information
- Sample data for each field
- Raw JSON schema viewer

## Advanced Features

### Multiple Sources

You can manage multiple independent data sources:

```bash
# Source 1: Sales data
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=sales_2025" \
  -F "file=@sales.txt"

# Source 2: Customer data
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=customers_2025" \
  -F "file=@customers.txt"

# Query each independently
curl "http://localhost:8002/api/schema?source_id=sales_2025"
curl "http://localhost:8002/api/schema?source_id=customers_2025"
```

### Error Handling

The system provides detailed error messages:

```json
{
  "status": "error",
  "error_type": "ValidationError",
  "error_message": "Unsupported file type: .xlsx"
}
```

Common errors:
- **Unsupported file type**: Only .txt, .pdf, .md allowed
- **No data found**: File contains no structured data
- **Schema not found**: Source ID doesn't exist (upload first)
- **Query execution error**: Invalid query syntax

## Performance Tips

1. **File Size**: Files under 10MB process quickly
2. **Complex Queries**: Use DB queries for complex aggregations
3. **Schema Evolution**: Upload related data to same source_id
4. **NL Queries**: Keep questions simple and specific

## Troubleshooting

### Upload Taking Too Long
- Check file size (large files take longer)
- Verify Ollama is running: `ps aux | grep ollama`
- Check logs: `tail -f /var/log/supervisor/etl_backend.err.log`

### Query Not Working
- Verify source_id exists: `GET /api/schema?source_id=...`
- Check query syntax
- Review query history for past errors

### Schema Not Updating
- Ensure using same source_id
- Check upload was successful
- View schema version number

## API Reference

### POST /api/upload
Upload and process file

**Parameters:**
- `source_id` (form): Unique identifier
- `file` (multipart): File to upload

**Response:** Upload result with schema

### GET /api/schema
Get schema for source

**Parameters:**
- `source_id` (query): Source identifier

**Response:** Schema details

### POST /api/query
Execute query

**Body:**
```json
{
  "source_id": "string",
  "query_type": "NL" | "DB",
  "query_text": "string"
}
```

**Response:** Query results

### GET /api/records
Get records for source

**Parameters:**
- `source_id` (query): Source identifier
- `query_id` (query, optional): Specific query ID

**Response:** List of records

### GET /api/history/uploads
Get upload history

**Parameters:**
- `source_id` (query): Source identifier

**Response:** Upload log

### GET /api/history/queries
Get query history

**Parameters:**
- `source_id` (query): Source identifier

**Response:** Query log

## Testing

### Test Files Available

1. `/app/test_data/mixed_data.txt` - All three data types
2. `/app/test_data/products.txt` - JSON only
3. `/app/test_data/employees.txt` - CSV only

### Quick Test

```bash
# Test upload
curl -X POST http://localhost:8002/api/upload \
  -F "source_id=test" \
  -F "file=@/app/test_data/mixed_data.txt"

# Test schema
curl "http://localhost:8002/api/schema?source_id=test"

# Test query
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{"source_id":"test","query_type":"DB","query_text":"{\"operation\":\"find\",\"filter\":{},\"projection\":{\"_id\":0}}"}'
```

## Production Considerations

### Security
- Add authentication/authorization
- Validate file contents
- Sanitize user inputs
- Rate limiting

### Scalability
- Use message queue (Celery) for async processing
- MongoDB replica sets
- Caching layer (Redis)
- Load balancing

### Monitoring
- Application metrics
- Query performance tracking
- Error rate monitoring
- Resource usage alerts

## Support

- View logs: `/var/log/supervisor/etl_backend.*.log`
- API docs: http://localhost:8002/docs
- Check service status: `sudo supervisorctl status`
