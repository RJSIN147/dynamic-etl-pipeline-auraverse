"""FastAPI server for ETL pipeline."""
from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import shutil

from modules.etl_pipeline import ETLPipeline
from modules.schema_manager import SchemaManager
from modules.query_executor import QueryExecutor

# Setup
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'etl_database')]

# Initialize components
etl_pipeline = ETLPipeline(db)
schema_manager = SchemaManager(db)
query_executor = QueryExecutor(db)

# FastAPI app
app = FastAPI(title="ETL Pipeline API")
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Models
class QueryRequest(BaseModel):
    source_id: str
    query_type: str  # "NL" or "DB"
    query_text: str

class UploadResponse(BaseModel):
    source_id: Optional[str] = None
    status: str
    parsed_summary: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

class SchemaResponse(BaseModel):
    source_id: str
    schema: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    source_id: str
    input_query_type: Optional[str] = None
    natural_language_query: Optional[str] = None
    db_query: Optional[str] = None
    db_query_translated: Optional[str] = None
    execution_result: Optional[List[Dict[str, Any]]] = None
    error: Optional[Dict[str, str]] = None

# Endpoints
@api_router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_id: str = Form(...)
):
    """Upload and process a file through ETL pipeline.
    
    Accepts: .txt, .pdf, .md files containing HTML, JSON, CSV data
    """
    logger.info(f"Received upload request: source_id={source_id}, filename={file.filename}")
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.txt', '.pdf', '.md']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Only .txt, .pdf, .md allowed."
        )
    
    # Save uploaded file
    file_path = UPLOAD_DIR / f"{source_id}_{file.filename}"
    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    finally:
        file.file.close()
    
    # Process file through ETL pipeline
    result = await etl_pipeline.process_file(str(file_path), source_id)
    
    return result

@api_router.get("/schema", response_model=SchemaResponse)
async def get_schema(source_id: str = Query(...)):
    """Get schema for a source."""
    schema = await schema_manager.get_schema(source_id)
    
    if not schema:
        raise HTTPException(
            status_code=404,
            detail=f"No schema found for source_id={source_id}"
        )
    
    return {
        "source_id": source_id,
        "schema": schema
    }

@api_router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a query (Natural Language or Direct DB query)."""
    logger.info(f"Query request: {request.model_dump()}")
    
    # Get schema
    schema = await schema_manager.get_schema(request.source_id)
    if not schema:
        raise HTTPException(
            status_code=404,
            detail=f"No schema found for source_id={request.source_id}"
        )
    
    # Execute query
    if request.query_type == "NL":
        result = await query_executor.execute_nl_query(
            request.source_id,
            request.query_text,
            schema
        )
    elif request.query_type == "DB":
        result = await query_executor.execute_db_query(
            request.source_id,
            request.query_text,
            schema
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="query_type must be 'NL' or 'DB'"
        )
    
    return result

@api_router.get("/records")
async def get_records(
    source_id: str = Query(...),
    query_id: Optional[str] = Query(None)
):
    """Get records for a source.
    
    If query_id is provided, returns results for that query.
    Otherwise, returns all records for the source.
    """
    # Get all data collections
    schema = await schema_manager.get_schema(source_id)
    if not schema:
        raise HTTPException(
            status_code=404,
            detail=f"No schema found for source_id={source_id}"
        )
    
    all_records = []
    collections = schema.get('collections', {})
    
    for collection_name in collections.keys():
        collection = db[collection_name]
        records = await collection.find(
            {"_source_id": source_id},
            {"_id": 0}
        ).to_list(1000)
        all_records.extend(records)
    
    return {
        "source_id": source_id,
        "query_id": query_id,
        "records": all_records
    }

@api_router.get("/history/uploads")
async def get_upload_history(source_id: str = Query(...)):
    """Get upload history for a source."""
    history = await etl_pipeline.get_upload_history(source_id)
    return {
        "source_id": source_id,
        "uploads": history
    }

@api_router.get("/history/queries")
async def get_query_history(source_id: str = Query(...)):
    """Get query history for a source."""
    history = await query_executor.get_query_history(source_id)
    return {
        "source_id": source_id,
        "queries": history
    }

@api_router.get("/")
async def root():
    return {"message": "ETL Pipeline API", "status": "running"}

# Include router
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
