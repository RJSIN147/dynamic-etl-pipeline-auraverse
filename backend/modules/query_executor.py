"""Query executor for running MongoDB queries."""
import logging
import json
from typing import Dict, Any, List
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class QueryExecutor:
    """Execute queries against MongoDB."""
    
    def __init__(self, db):
        self.db = db
        self.ollama_client = OllamaClient()
        self.queries_collection = db.queries
    
    async def execute_nl_query(self, source_id: str, natural_language: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute natural language query by converting to MongoDB query."""
        try:
            # Translate NL to MongoDB query
            query_json = self.ollama_client.translate_nl_to_query(natural_language, schema)
            logger.info(f"Translated query: {query_json}")
            
            # Parse query
            query_obj = json.loads(query_json)
            
            # Execute query
            results = await self._execute_mongo_query(query_obj, schema)
            
            # Log query
            await self._log_query(source_id, "NL", natural_language, query_json, len(results), None)
            
            return {
                "source_id": source_id,
                "input_query_type": "NL",
                "natural_language_query": natural_language,
                "db_query_translated": query_json,
                "execution_result": results,
                "error": None
            }
        except Exception as e:
            logger.error(f"Error executing NL query: {e}")
            await self._log_query(source_id, "NL", natural_language, None, 0, str(e))
            return {
                "source_id": source_id,
                "error": {
                    "type": "QueryExecutionError",
                    "message": str(e)
                }
            }
    
    async def execute_db_query(self, source_id: str, query_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MongoDB query directly."""
        try:
            # Parse query
            query_obj = json.loads(query_text)
            
            # Execute query
            results = await self._execute_mongo_query(query_obj, schema)
            
            # Log query
            await self._log_query(source_id, "DB", query_text, query_text, len(results), None)
            
            return {
                "source_id": source_id,
                "input_query_type": "DB",
                "db_query": query_text,
                "execution_result": results,
                "error": None
            }
        except Exception as e:
            logger.error(f"Error executing DB query: {e}")
            await self._log_query(source_id, "DB", query_text, None, 0, str(e))
            return {
                "source_id": source_id,
                "error": {
                    "type": "QueryExecutionError",
                    "message": str(e)
                }
            }
    
    async def _execute_mongo_query(self, query_obj: Dict[str, Any], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute parsed MongoDB query."""
        operation = query_obj.get('operation', 'find')
        
        # Determine collection to query
        collections = schema.get('collections', {})
        if not collections:
            return []
        
        # Query all relevant collections
        all_results = []
        
        if operation == 'find':
            filter_query = query_obj.get('filter', {})
            projection = query_obj.get('projection', {"_id": 0})
            
            for collection_name in collections.keys():
                collection = self.db[collection_name]
                results = await collection.find(filter_query, projection).to_list(1000)
                all_results.extend(results)
        
        elif operation == 'aggregate':
            pipeline = query_obj.get('pipeline', [])
            
            for collection_name in collections.keys():
                collection = self.db[collection_name]
                results = await collection.aggregate(pipeline).to_list(1000)
                all_results.extend(results)
        
        return all_results
    
    async def _log_query(self, source_id: str, query_type: str, original_query: str, 
                        translated_query: str, result_count: int, error: str):
        """Log query execution."""
        from datetime import datetime, timezone
        
        log_entry = {
            "source_id": source_id,
            "query_type": query_type,
            "original_query": original_query,
            "translated_query": translated_query,
            "result_count": result_count,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.queries_collection.insert_one(log_entry)
    
    async def get_query_history(self, source_id: str) -> List[Dict[str, Any]]:
        """Get query history for a source."""
        queries = await self.queries_collection.find(
            {"source_id": source_id},
            {"_id": 0}
        ).to_list(1000)
        return queries
