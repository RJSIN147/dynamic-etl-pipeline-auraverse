# Dynamic ETL Pipeline System

## 🎯 Overview
A dynamic ETL pipeline system that ingests files containing mixed data formats (HTML, JSON, CSV) and provides:
- ✅ Automatic schema generation and evolution
- ✅ Database-agnostic data storage (MongoDB)
- ✅ Natural language query interface using local LLM (Ollama + Qwen)
- ✅ FastAPI backend with comprehensive REST API
- ✅ Streamlit frontend for easy interaction
- ✅ Fully local - no cloud dependencies

## 🏗️ Architecture

### Backend (FastAPI)
- **File Parser**: Extracts text from .txt, .pdf, .md files
- **Data Extractor**: Identifies and extracts HTML, JSON, CSV fragments using hybrid SLM + heuristic approach
- **Data Cleaner**: Canonicalizes fields, deduplicates records
- **Schema Manager**: Generates and updates database-agnostic schemas
- **Query Executor**: Executes both natural language and direct MongoDB queries

### Frontend (Streamlit)
- File upload interface with drag-and-drop
- Schema viewer with field inspector
- Dual query interface (NL and DB queries)
- Upload and query history with logs

### Database (MongoDB)
- Dynamic collections based on extracted data
- Automatic schema versioning and evolution
- Complete audit trails for uploads and queries

### LLM Integration (Ollama)
- **SLM**: qwen2.5:0.5b for intelligent data type detection
- **LLM**: qwen2.5:0.5b for NL to MongoDB query translation
- Fully local, no external API dependencies, completely free

---

## 🚀 Complete Setup Guide

### Step 1: Prerequisites

#### Install Python 3.11+
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux/Mac**: Usually pre-installed

#### Install MongoDB
- **Windows**: 
  1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
  2. Install and start MongoDB service
  3. Verify: Open Command Prompt and run `mongosh` or check services

- **Linux**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install mongodb
  sudo systemctl start mongodb
  
  # Or use Docker
  docker run -d -p 27017:27017 --name mongodb mongo:latest
  ```

- **Mac**:
  ```bash
  brew tap mongodb/brew
  brew install mongodb-community
  brew services start mongodb-community
  ```

#### Install Ollama
- **Windows**: 
  1. Download from [ollama.com](https://ollama.com/download)
  2. Install the Windows executable
  3. Ollama will start automatically

- **Linux/Mac**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

### Step 2: Install Dependencies

Open terminal/command prompt and navigate to the project:

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies (if needed)
cd ../frontend_streamlit
pip install -r requirements.txt
```

### Step 3: Pull Ollama Model

In a new terminal/command prompt:

```bash
# Pull the Qwen 2.5 0.5B model (small and fast)
ollama pull qwen2.5:0.5b
```

**Note**: This will download ~400MB. First pull takes a few minutes.

### Step 4: Configure MongoDB Connection

The default configuration connects to `mongodb://localhost:27017`. If your MongoDB is on a different host/port, update:

**File**: `backend/.env`
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="etl_database"
CORS_ORIGINS="*"
```

### Step 5: Start the Application

#### Option A: Using Simple Commands (Recommended for Windows)

**Terminal 1 - Start Backend:**
```bash
cd backend
fastapi dev main.py
```

Backend will start on: **http://localhost:8000**

**Terminal 2 - Start Frontend:**
```bash
cd frontend_streamlit
streamlit run app.py
```

Frontend will start on: **http://localhost:8501**

**Terminal 3 - Ensure Ollama is Running:**
```bash
# Windows: Ollama should auto-start, but verify:
ollama serve

# Linux/Mac:
ollama serve
```

#### Option B: Using Production Commands

**Backend (Production):**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (Production):**
```bash
cd frontend_streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Step 6: Verify Installation

1. **Check MongoDB**: Should be running on port 27017
   ```bash
   # Windows/Linux/Mac
   mongosh
   # or
   mongo
   ```

2. **Check Ollama**: Should be running on port 11434
   ```bash
   curl http://localhost:11434/api/tags
   # Should return list of models including qwen2.5:0.5b
   ```

3. **Check Backend**: Open http://localhost:8000/docs
   - Should show FastAPI Swagger documentation

4. **Check Frontend**: Open http://localhost:8501
   - Should show Streamlit app with "Dynamic ETL Pipeline System" title

---

## 📖 Quick Start Guide

### Upload Your First File

#### Step 1: Create a Test File

Create `test_data.txt` with mixed content:

```
Product Catalog (JSON):
{"product_id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"}
{"product_id": 2, "name": "Mouse", "price": 29.99, "category": "Accessories"}
{"product_id": 3, "name": "Keyboard", "price": 79.99, "category": "Accessories"}

Customer List (CSV):
customer_id,name,email,country
C001,Alice Johnson,alice@email.com,USA
C002,Bob Smith,bob@email.com,Canada
C003,Carol Davis,carol@email.com,UK

Store Locations (HTML):
<table>
  <tr><th>Store ID</th><th>City</th><th>Manager</th></tr>
  <tr><td>S001</td><td>New York</td><td>John Doe</td></tr>
  <tr><td>S002</td><td>Los Angeles</td><td>Jane Smith</td></tr>
</table>
```

#### Step 2: Upload via Streamlit UI

1. Open http://localhost:8501
2. Go to "Upload & Process" page
3. Enter Source ID: `my_first_upload`
4. Click "Browse files" and select your `test_data.txt`
5. Click "🚀 Process File"

**Expected Result:**
- Status: ✅ Success
- Fragments: 3 (JSON, CSV, HTML)
- Records: 8 total
- Schema: Version 1 created

#### Step 3: View Schema

1. Navigate to "View Schema" page
2. Click "🔄 Fetch Schema"
3. See schema with 3 collections:
   - `json_data`: product_id, name, price, category
   - `csv_data`: customer_id, name, email, country
   - `html_data`: table structure

#### Step 4: Query Data

**Natural Language Query:**
1. Go to "Query Data" page
2. Select "Natural Language"
3. Enter: `Show me all products`
4. Click "🚀 Execute Query"
5. View translated MongoDB query and results

**Direct MongoDB Query:**
1. Select "Direct MongoDB Query"
2. Enter:
   ```json
   {"operation": "find", "filter": {"price": {"$gt": 50}}, "projection": {"_id": 0}}
   ```
3. Click "🚀 Execute Query"
4. View results (Laptop and Keyboard with price > 50)

---

## 📚 API Documentation

### Base URL
- **Backend API**: `http://localhost:8000/api`
- **API Docs**: `http://localhost:8000/docs`

### Endpoints

#### 1. Upload File
```bash
POST /api/upload

# Example (Windows PowerShell):
curl -X POST "http://localhost:8000/api/upload" `
  -F "source_id=my_project" `
  -F "file=@C:\path\to\your\file.txt"

# Example (Linux/Mac/Git Bash):
curl -X POST http://localhost:8000/api/upload \
  -F "source_id=my_project" \
  -F "file=@/path/to/your/file.txt"
```

**Response:**
```json
{
  "source_id": "my_project",
  "status": "success",
  "parsed_summary": {
    "fragments": [...],
    "total_fragments": 3,
    "total_records": 8,
    "data_types": ["json", "csv", "html"]
  },
  "schema": {...}
}
```

#### 2. Get Schema
```bash
GET /api/schema?source_id=my_project

# Example:
curl "http://localhost:8000/api/schema?source_id=my_project"
```

#### 3. Execute Query
```bash
POST /api/query

# Natural Language Query:
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"source_id":"my_project","query_type":"NL","query_text":"Show me all products"}'

# Direct MongoDB Query:
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"source_id":"my_project","query_type":"DB","query_text":"{\"operation\":\"find\",\"filter\":{},\"projection\":{\"_id\":0}}"}'
```

#### 4. Get Records
```bash
GET /api/records?source_id=my_project

curl "http://localhost:8000/api/records?source_id=my_project"
```

#### 5. View History
```bash
# Upload history
GET /api/history/uploads?source_id=my_project

# Query history
GET /api/history/queries?source_id=my_project
```

---

## 🔍 How It Works

### Data Extraction Process

1. **File Upload**: User uploads .txt, .pdf, or .md file
2. **Text Extraction**: System extracts plain text
3. **SLM Detection**: Ollama model identifies data type boundaries
4. **Heuristic Parsing**: Specialized parsers extract structured data
   - JSON: `json` module with malformed JSON fixes
   - CSV: `csv` module with delimiter detection
   - HTML: BeautifulSoup with table extraction
5. **Data Cleaning**: Field normalization, type inference, deduplication
6. **Schema Generation**: Automatic schema creation with field types
7. **Data Loading**: Insert into MongoDB collections
8. **Ready for Queries**: Data available via NL or DB queries

### Schema Evolution

When uploading multiple files to the same `source_id`:
- **Version 1**: Initial schema created
- **Version 2**: New fields added, existing fields merged
- **Version N**: Continuous evolution with backward compatibility

Example:
```
Upload 1: {"id": 1, "name": "Product A"} → Schema v1
Upload 2: {"id": 2, "name": "Product B", "price": 99} → Schema v2 (adds "price")
Upload 3: CSV with category field → Schema v3 (adds "category")
```

---

## 🎨 Streamlit UI Features

### Page 1: Upload & Process
- Drag-and-drop file upload
- Source ID management
- Real-time processing status
- Fragment preview with samples
- Schema version display

### Page 2: View Schema
- Schema metadata viewer
- Collection browser
- Field type inspector
- Sample data display
- Raw JSON export

### Page 3: Query Data
- **Natural Language Mode**:
  - Plain English queries
  - Automatic MongoDB translation
  - Query explanation
- **Direct Query Mode**:
  - JSON-based MongoDB queries
  - Syntax examples
  - Query validation

### Page 4: History
- Upload logs with timestamps
- Query execution history
- Error tracking
- Performance metrics

---

## 🧪 Testing

### Test Files Included

1. **`/app/test_data/mixed_data.txt`**: All three data types
2. **`/app/test_data/products.txt`**: JSON only
3. **`/app/test_data/employees.txt`**: CSV only

### Quick Test Commands

```bash
# Test upload
curl -X POST http://localhost:8000/api/upload \
  -F "source_id=test_run" \
  -F "file=@test_data/mixed_data.txt"

# Test schema fetch
curl "http://localhost:8000/api/schema?source_id=test_run"

# Test query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"source_id":"test_run","query_type":"DB","query_text":"{\"operation\":\"find\",\"filter\":{},\"projection\":{\"_id\":0}}"}'
```

---

## 🔧 Configuration

### Backend Port (default: 8000)
Change in command:
```bash
fastapi dev main.py --port 8080
```

### Frontend Port (default: 8501)
Change in command:
```bash
streamlit run app.py --server.port 8502
```

### MongoDB Connection
Edit `backend/.env`:
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="your_database_name"
```

### Ollama Model
Change model in `backend/modules/ollama_client.py`:
```python
def __init__(self, model: str = "qwen2.5:0.5b"):
```

Available models:
- `qwen2.5:0.5b` - Fast, 400MB (recommended)
- `qwen2.5:1.5b` - Balanced, 1GB
- `qwen2.5:3b` - Better accuracy, 2GB
- `llama3.2` - Alternative, 2GB

---

## ❓ Troubleshooting

### MongoDB Connection Error
```
Error: Cannot connect to MongoDB
```
**Solution:**
1. Verify MongoDB is running: `mongosh` or check Windows Services
2. Check connection string in `backend/.env`
3. Ensure port 27017 is not blocked by firewall

### Ollama Not Responding
```
Error: Connection refused to Ollama
```
**Solution:**
1. Start Ollama: `ollama serve`
2. Verify: `curl http://localhost:11434/api/tags`
3. Pull model again: `ollama pull qwen2.5:0.5b`

### File Upload Timeout
```
Error: Request timeout
```
**Solution:**
1. Check file size (keep under 10MB)
2. Verify Ollama is running
3. Check logs: `backend/logs/` or console output

### Natural Language Query Not Working
```
Error: Query translation failed
```
**Solution:**
1. Ensure Ollama is running
2. Try simpler queries first
3. Use Direct MongoDB Query as alternative
4. Check Ollama logs

### Port Already in Use
```
Error: Address already in use
```
**Solution:**
1. Change port in startup command
2. Or kill existing process:
   - Windows: `taskkill /F /IM python.exe`
   - Linux/Mac: `lsof -ti:8000 | xargs kill -9`

---

## 📊 Performance

- **Small files (<1MB)**: Process in 2-5 seconds
- **Medium files (1-10MB)**: Process in 10-30 seconds
- **Large files (10-50MB)**: Process in 1-3 minutes
- **SLM detection**: Adds 2-5 seconds per file
- **Query execution**: 100-500ms for simple queries

---

## 📝 Additional Documentation

- **`USAGE_GUIDE.md`**: Detailed usage examples and workflows
- **`SCHEMA_EVOLUTION_EXAMPLE.md`**: Step-by-step schema evolution demonstration
- **API Docs**: http://localhost:8000/docs (interactive Swagger UI)

---

## 🚀 Production Deployment

For production use, consider:
1. **Security**: Add authentication (JWT, OAuth)
2. **Scalability**: Use Celery for async processing
3. **Database**: MongoDB replica sets for high availability
4. **Monitoring**: Add APM (Application Performance Monitoring)
5. **Caching**: Redis for query result caching
6. **Load Balancing**: Nginx or similar for multiple instances

---

## 📄 License & Support

This is an evaluation project demonstrating ETL pipeline capabilities.

For issues or questions:
- Check logs in console output
- Review API documentation at http://localhost:8000/docs
- Verify all services are running (MongoDB, Ollama, Backend, Frontend)
