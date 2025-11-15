# Windows Setup Guide - Dynamic ETL Pipeline System

## Quick Start (3 Steps)

### Step 1: Install Prerequisites

1. **Install Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: Open Command Prompt and run `python --version`

2. **Install MongoDB**
   - Download MongoDB Community Server: https://www.mongodb.com/try/download/community
   - Install with default settings
   - MongoDB will start automatically as a Windows service
   - Verify: Open Command Prompt and run `mongosh`

3. **Install Ollama**
   - Download from: https://ollama.com/download
   - Run the installer (OllamaSetup.exe)
   - Ollama will start automatically
   - Verify: Open Command Prompt and run `ollama --version`

### Step 2: Install Python Dependencies

Open Command Prompt in the project folder:

```cmd
cd backend
pip install -r requirements.txt

cd ..
cd frontend_streamlit
pip install -r requirements.txt
```

### Step 3: Pull Ollama Model

```cmd
ollama pull qwen2.5:0.5b
```

This downloads ~400MB. First time takes a few minutes.

---

## Running the Application

### Option 1: Using Batch Files (Easiest)

**Start Everything at Once:**
```cmd
start_all.bat
```

This opens 3 windows:
- Ollama service
- Backend API (FastAPI)
- Frontend UI (Streamlit)

**Or Start Individually:**
```cmd
start_backend.bat  # Starts FastAPI backend
start_frontend.bat # Starts Streamlit frontend
```

### Option 2: Manual Start (3 Terminals)

**Terminal 1 - Ollama:**
```cmd
ollama serve
```

**Terminal 2 - Backend:**
```cmd
cd backend
fastapi dev main.py
```

**Terminal 3 - Frontend:**
```cmd
cd frontend_streamlit
streamlit run app.py
```

---

## Access the Application

- **Frontend UI**: http://localhost:8501
- **Backend API Docs**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000/api

---

## Test the Application

### Quick Test

1. Open http://localhost:8501 in your browser
2. Create a test file `test.txt`:

```
Products:
{"id": 1, "name": "Laptop", "price": 999}
{"id": 2, "name": "Mouse", "price": 29}

Customers:
id,name,email
1,John,john@email.com
2,Jane,jane@email.com
```

3. Upload the file:
   - Source ID: `test`
   - Select `test.txt`
   - Click "Process File"

4. View Schema:
   - Navigate to "View Schema"
   - Click "Fetch Schema"

5. Query Data:
   - Navigate to "Query Data"
   - Try: "Show me all products"
   - Click "Execute Query"

---

## Troubleshooting

### MongoDB Not Running

**Check Status:**
1. Open Services (Win + R, type `services.msc`)
2. Find "MongoDB Server"
3. Start if stopped

**Or use Command:**
```cmd
net start MongoDB
```

### Ollama Not Responding

**Restart Ollama:**
```cmd
taskkill /F /IM ollama.exe
ollama serve
```

### Port Already in Use

**Kill Process on Port 8000:**
```cmd
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>
```

**Kill Process on Port 8501:**
```cmd
netstat -ano | findstr :8501
taskkill /F /PID <PID_NUMBER>
```

### Module Not Found Error

**Reinstall Dependencies:**
```cmd
cd backend
pip install --force-reinstall -r requirements.txt
```

### Ollama Model Not Found

**Pull Model Again:**
```cmd
ollama pull qwen2.5:0.5b
```

**List Downloaded Models:**
```cmd
ollama list
```

---

## Firewall Settings

If you can't access the application from another computer on your network:

1. Open Windows Firewall
2. Allow inbound connections on:
   - Port 8000 (Backend)
   - Port 8501 (Frontend)
   - Port 27017 (MongoDB)
   - Port 11434 (Ollama)

---

## Stopping the Application

**Close all terminal windows** or:

```cmd
taskkill /F /IM python.exe
taskkill /F /IM ollama.exe
```

---

## Performance Tips

1. **First Query is Slow**: Ollama needs to load the model (30 seconds)
2. **Subsequent Queries**: Much faster (2-5 seconds)
3. **Large Files**: Process smaller chunks (<5MB)
4. **SSD Recommended**: For faster file processing

---

## System Requirements

- **OS**: Windows 10/11
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **CPU**: Modern dual-core or better

---

## Next Steps

1. Read full documentation: `README.md`
2. See usage examples: `USAGE_GUIDE.md`
3. Understand schema evolution: `SCHEMA_EVOLUTION_EXAMPLE.md`
4. Explore API: http://localhost:8000/docs

---

## Support

If you encounter issues:

1. Check all services are running
2. Verify Python version: `python --version` (should be 3.11+)
3. Check MongoDB: `mongosh`
4. Check Ollama: `ollama list`
5. View logs in the terminal windows
