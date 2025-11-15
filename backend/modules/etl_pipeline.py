"""Main ETL pipeline orchestrator."""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

from .file_parser import FileParser
from .data_extractor import DataExtractor
from .data_cleaner import DataCleaner
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)

class ETLPipeline:
    """Main ETL pipeline for processing uploaded files."""
    
    def __init__(self, db):
        self.db = db
        self.file_parser = FileParser()
        self.data_extractor = DataExtractor(use_slm=True)
        self.data_cleaner = DataCleaner()
        self.schema_manager = SchemaManager(db)
        self.uploads_collection = db.uploads
    
    async def process_file(self, file_path: str, source_id: str) -> Dict[str, Any]:
        """Process uploaded file through ETL pipeline.
        
        Steps:
        1. Parse file (extract text from .txt, .pdf, .md)
        2. Extract data fragments (HTML, JSON, CSV)
        3. Clean and canonicalize data
        4. Generate/update schema
        5. Load data into database
        6. Return processing summary
        """
        logger.info(f"Starting ETL pipeline for source_id={source_id}, file={file_path}")
        
        try:
            # Step 1: Parse file
            content, file_type = self.file_parser.parse_file(file_path)
            logger.info(f"Parsed {file_type} file, length={len(content)} chars")
            
            # Step 2: Extract fragments
            fragments = self.data_extractor.extract_all_fragments(content, source_id)
            logger.info(f"Extracted {len(fragments)} fragments")
            
            if not fragments:
                return {
                    "status": "error",
                    "error_type": "NoDataFound",
                    "error_message": "No structured data (HTML/JSON/CSV) found in file"
                }
            
            # Step 3: Clean data
            all_records = []
            for fragment in fragments:
                parsed_data = fragment.get('parsed_data', [])
                if isinstance(parsed_data, list):
                    records = parsed_data
                elif isinstance(parsed_data, dict):
                    records = [parsed_data]
                else:
                    continue
                
                # Clean records
                if records and isinstance(records[0], dict):
                    cleaned = self.data_cleaner.clean_records(records)
                    all_records.extend(cleaned)
                    fragment['cleaned_records'] = cleaned
            
            logger.info(f"Cleaned {len(all_records)} total records")
            
            # Step 4: Generate schema
            schema = await self.schema_manager.generate_schema(source_id, fragments, all_records)
            
            # Step 5: Load data into database
            await self._load_data(source_id, fragments)
            
            # Step 6: Log upload
            await self._log_upload(source_id, file_path, file_type, fragments, len(all_records))
            
            # Create summary
            parsed_summary = {
                "fragments": [
                    {
                        "type": f['type'],
                        "start_line": f['start_line'],
                        "end_line": f['end_line'],
                        "record_count": len(f.get('cleaned_records', [])),
                        "sample": f.get('cleaned_records', [])[:2] if f.get('cleaned_records') else []
                    }
                    for f in fragments
                ],
                "total_fragments": len(fragments),
                "total_records": len(all_records),
                "data_types": list(set(f['type'] for f in fragments))
            }
            
            return {
                "source_id": source_id,
                "status": "success",
                "parsed_summary": parsed_summary,
                "schema": schema
            }
            
        except Exception as e:
            logger.error(f"ETL pipeline error: {e}", exc_info=True)
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
    
    async def _load_data(self, source_id: str, fragments: List[Dict[str, Any]]):
        """Load cleaned data into database collections."""
        for fragment in fragments:
            frag_type = fragment['type']
            cleaned_records = fragment.get('cleaned_records', [])
            
            if not cleaned_records:
                continue
            
            # Create collection name
            collection_name = f"{frag_type}_data"
            collection = self.db[collection_name]
            
            # Create copies of records to avoid modifying originals
            records_to_insert = []
            for record in cleaned_records:
                record_copy = record.copy()
                record_copy['_source_id'] = source_id
                record_copy['_uploaded_at'] = datetime.now(timezone.utc).isoformat()
                records_to_insert.append(record_copy)
            
            # Insert records
            if records_to_insert:
                await collection.insert_many(records_to_insert)
                logger.info(f"Loaded {len(records_to_insert)} records into {collection_name}")
    
    async def _log_upload(self, source_id: str, file_path: str, file_type: str, 
                         fragments: List[Dict[str, Any]], record_count: int):
        """Log upload event."""
        log_entry = {
            "source_id": source_id,
            "file_path": os.path.basename(file_path),
            "file_type": file_type,
            "fragments_count": len(fragments),
            "record_count": record_count,
            "data_types": list(set(f['type'] for f in fragments)),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.uploads_collection.insert_one(log_entry)
    
    async def get_upload_history(self, source_id: str) -> List[Dict[str, Any]]:
        """Get upload history for a source."""
        uploads = await self.uploads_collection.find(
            {"source_id": source_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(100)
        return uploads
