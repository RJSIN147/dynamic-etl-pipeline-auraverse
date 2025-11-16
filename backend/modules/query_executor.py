"""Query executor for running MongoDB queries."""
import logging
import json
from typing import Dict, Any, List, Set
from bson.objectid import ObjectId
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class QueryExecutor:
    """Execute queries against MongoDB."""
    
    def __init__(self, db):
        self.db = db
        self.ollama_client = OllamaClient()
        self.queries_collection = db.queries

    def _get_fields_from_query(self, query_part: Dict[str, Any]) -> Set[str]:
        """Recursively extract all field keys used in a filter or projection."""
        fields = set()
        for key, value in query_part.items():
            if key.startswith('$'):
                # Handle operators like $or, $and
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            fields.update(self._get_fields_from_query(item))
            elif isinstance(value, dict):
                # Handle nested queries like {"field": {"$gt": 10}}
                # We only care about the top-level field name
                fields.add(key)
            else:
                # Standard key: "field": "value" or in projection "field": 1
                if key != "_id":
                    fields.add(key)
        return fields
    
    async def execute_nl_query(self, source_id: str, natural_language: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute natural language query by converting to MongoDB query."""
        query_json = None
        try:
            # Translate NL to MongoDB query
            query_json = self.ollama_client.translate_nl_to_query(natural_language, schema)
            logger.info(f"Translated query: {query_json}")
            
            # --- FIX 1: Add graceful JSON parsing error handling ---
            try:
                query_obj = json.loads(query_json)
            except json.JSONDecodeError as json_err:
                logger.error(f"LLM returned invalid JSON: {json_err}. Query: {query_json}")
                raise ValueError(f"AI failed to generate valid JSON. Error: {json_err}")
            
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
            await self._log_query(source_id, "NL", natural_language, query_json, 0, str(e))
            return {
                "source_id": source_id,
                "input_query_type": "NL",
                "natural_language_query": natural_language,
                "db_query_translated": query_json,
                "error": {
                    "type": type(e).__name__,
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
                "input_query_type": "DB",
                "db_query": query_text,
                "error": {
                    "type": "QueryExecutionError",
                    "message": str(e)
                }
            }
    
    def _serialize_mongo_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively convert ObjectId to str for JSON serialization."""
        serialized_results = []
        for record in results:
            new_record = {}
            for key, value in record.items():
                if isinstance(value, ObjectId):
                    new_record[key] = str(value)
                elif isinstance(value, dict):
                    # Recurse for nested dicts (if any)
                    new_record[key] = self._serialize_mongo_results([value])[0]
                elif isinstance(value, list):
                    # Recurse for nested lists (if any)
                    new_list = []
                    for item in value:
                        if isinstance(item, dict):
                            new_list.append(self._serialize_mongo_results([item])[0])
                        else:
                            new_list.append(item)
                    new_record[key] = new_list
                else:
                    new_record[key] = value
            serialized_results.append(new_record)
        return serialized_results

    async def _execute_mongo_query(self, query_obj: Dict[str, Any], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute parsed MongoDB query intelligently by checking schema.
        """
        operation = query_obj.get('operation', 'find')
        collections_in_schema = schema.get('collections', {})
        if not collections_in_schema:
            return []

        all_results = []
        
        if operation == 'find':
            filter_query = query_obj.get('filter', {})
            projection = query_obj.get('projection', {"_id": 0})
            
            # --- FIX 2: "Smart Executor" Logic ---
            
            # 1. Get all fields used in the filter and projection
            fields_in_filter = self._get_fields_from_query(filter_query)
            fields_in_projection = self._get_fields_from_query(projection)
            
            logger.info(f"Fields in filter: {fields_in_filter}")
            logger.info(f"Fields in projection: {fields_in_projection}")

            # 2. Iterate over collections and query only relevant ones
            for collection_name, coll_data in collections_in_schema.items():
                fields_in_this_collection = set(coll_data.get('fields', {}).keys())
                
                # Check 1: Do all FILTER fields exist in this collection?
                # If a filter exists, all its fields must be in the collection.
                if fields_in_filter and not fields_in_filter.issubset(fields_in_this_collection):
                    logger.info(f"Skipping {collection_name}: missing filter fields.")
                    continue
                
                # Check 2: If a projection exists, does this collection have AT LEAST ONE projected field?
                # This prevents returning empty {} for collections that match the filter (e.g., {})
                # but have none of the projected fields.
                if fields_in_projection and not fields_in_projection.intersection(fields_in_this_collection):
                    logger.info(f"Skipping {collection_name}: missing projection fields.")
                    continue
                
                # If we pass both checks, query this collection
                logger.info(f"Querying collection: {collection_name}")
                collection = self.db[collection_name]
                results = await collection.find(filter_query, projection).to_list(1000)
                all_results.extend(results)
        
        elif operation == 'aggregate':
            # Aggregations are complex. For now, we run them on all collections.
            # A smarter approach would be to parse the pipeline, but that's
            # much more complex. This remains as-is for now.
            pipeline = query_obj.get('pipeline', [])
            for collection_name in collections_in_schema.keys():
                collection = self.db[collection_name]
                try:
                    results = await collection.aggregate(pipeline).to_list(1000)
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"Aggregation failed on {collection_name}: {e}")

        
        return self._serialize_mongo_results(all_results)
    
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
        ).sort("timestamp", -1).to_list(1000)
        # Serialize results to handle any ObjectIds
        return self._serialize_mongo_results(queries)