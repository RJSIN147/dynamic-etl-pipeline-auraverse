# **Dynamic ETL Pipeline System**

A **local-first ETL (Extract, Transform, Load) system** that ingests files containing mixed, unstructured data, automatically generates a queryable schema, and provides a **Natural Language Query (NLQ)** interface.

This system ingests **.txt, .pdf, or .md** files and intelligently extracts structured data such as **JSON**, **CSV**, and **HTML tables**. All extracted data is cleaned, typed, and loaded into **MongoDB**, where it becomes instantly queryable using plain English.

---

## **Core Features**

### ✅ **Multi-Format Parsing**

Extracts **JSON**, **CSV**, and **HTML table** data from a single file, even if mixed.

### ✅ **Automatic Schema Evolution**

Generates and versions a schema **on the fly**.
If new files contain new fields, the system **merges** them into the existing schema instead of breaking.

### ✅ **Natural Language Query (NLQ)**

Uses a **local llama3:8b** model to translate plain English questions
(e.g., *“Show me revenue over 100000”*) into valid MongoDB queries.

### ✅ **Full History Tracking**

UI provides:

* Upload history
* Query history
* Complete schema versioning timeline

### ✅ **100% Local**

Everything runs on your machine:

* File Processing
* Database
* LLM
* Frontend + Backend

No data ever leaves your system.

---

# **Architecture**

The system consists of **three main local services**:

* **Frontend (Streamlit):** Upload files, view schema, run queries
* **Backend (FastAPI):** ETL pipeline, schema management, query execution
* **Database (MongoDB):** Flexible storage for evolving schemas
* **LLM (Ollama):** NLQ → MongoDB query translation

---

### **System Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│                   (Streamlit - Port 8501)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Upload  │  │  Schema  │  │  Query   │  │ History  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Requests
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Port 8000)              │
│  ┌────────────────────────────────────────────────────┐     │
│  │                    ETL Pipeline                    │     │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │     │
│  │  │Parse │→ │Extract│→│Clean │→ │Schema│→ │Load  │  │     │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Query Executor (“Smart Executor”)        │     │
│  │  ┌──────────────┐  ┌──────────────┐                │     │
│  │  │   NL Query   │  │   DB Query   │                │     │
│  │  │   (via LLM)  │  │   (Direct)   │                │     │
│  │  └──────────────┘  └──────────────┘                │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────────┬───────────────────────┬────────────┘
                         │                       │
                         ↓                       ↓
                ┌────────────────┐      ┌───────────────┐
                │    MongoDB     │      │    Ollama     │
                │  (Port 27017)  │      │  (Port 11434) │
                │                │      │               │
                │  • json_data   │      │   llama3:8b   │
                │  • csv_data    │      │   NL → Query  │
                │  • html_data   │      │               │
                │  • schemas     │      └───────────────┘
                │  • uploads     │
                │  • queries     │
                │  • schema_history│
                └────────────────┘
```

---

# **Setup and Installation**

## **Step 1: Prerequisites**

You need the following installed:

* **Python 3.10+**
* **MongoDB**
  Must be running locally (`mongodb://localhost:27017`)
* **Ollama**
  Download from *ollama.com*

---

## **Step 2: Configure Environment**

In the **backend directory**:

1. Create a `.env` file
2. Add:

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="etl_database"
CORS_ORIGINS="*"
```

---

## **Step 3: Install Dependencies**

### Backend

```bash
# from backend/
pip install -r requirements.txt
```

### Frontend

```bash
# from frontend/
pip install -r requirements.txt
```

---

## **Step 4: Pull the LLM Model**

```bash
ollama pull llama3:8b
```

---

# **Running the Application**

You must run **three services** in three terminals.

---

## **Terminal 1 — Run Ollama**

Ensure Ollama is running (it usually autostarts):

```bash
ollama serve
```

---

## **Terminal 2 — Backend (FastAPI)**

```bash
cd backend
uvicorn main:app --reload
```

Backend will be available at:
**[http://localhost:8000](http://localhost:8000)**

---

## **Terminal 3 — Frontend (Streamlit)**

```bash
cd frontend
streamlit run app.py
```


