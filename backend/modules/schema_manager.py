"""Schema manager for generating and updating database schemas."""
import logging
from typing import List, Dict, Any, Set
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manage schema generation and evolution."""
    
    def __init__(self, db):
        self.db = db
        self.schemas_collection = db.schemas
        self.schema_history_collection = db.schema_history # <-- NEW: History Collection
    
    async def generate_schema(self, source_id: str, fragments: List[Dict[str, Any]], 
                             all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate database-agnostic schema from extracted data.
        
        This function now creates a historical record of the schema version
        before updating the main schema document.
        """
        # Get existing schema if any
        existing_schema = await self.schemas_collection.find_one(
            {"source_id": source_id},
            {"_id": 0}
        )
        
        # Infer schema from records
        # This function now correctly infers from the 'cleaned_records' key in fragments
        collections_schema = self._infer_collections_schema(fragments, all_records)
        
        # Determine data types present
        data_types = list(set(f['type'] for f in fragments))
        
        if existing_schema:
            # Update existing schema
            new_version = existing_schema.get('version', 1) + 1
            merged_collections = self._merge_schemas(
                existing_schema.get('collections', {}),
                collections_schema
            )
            
            schema = {
                "source_id": source_id,
                "version": new_version,
                "created_at": existing_schema['created_at'],
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "collections": merged_collections,
                "data_types_present": list(set(existing_schema.get('data_types_present', []) + data_types))
            }
        else:
            # Create new schema
            schema = {
                "source_id": source_id,
                "version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "collections": collections_schema,
                "data_types_present": data_types
            }
        
        # 1. Log Schema History (The key change for immutable history)
        # We save a copy of the new schema version here.
        schema_copy = schema.copy()
        # Ensure _id is not saved if it somehow slipped in
        if "_id" in schema_copy:
            del schema_copy["_id"]
        await self.schema_history_collection.insert_one(schema_copy)
        logger.info(f"Schema history logged for source_id={source_id}, version={schema['version']}")

        # 2. Save Current Schema (for quick lookup)
        await self.schemas_collection.update_one(
            {"source_id": source_id},
            {"$set": schema},
            upsert=True
        )
        
        logger.info(f"Schema generated and updated for source_id={source_id}, version={schema['version']}")
        return schema
    
    def _infer_collections_schema(self, fragments: List[Dict[str, Any]], 
                                 all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer schema for collections based on data fragments."""
        collections = {}
        
        # Group records by fragment type
        for fragment in fragments:
            frag_type = fragment['type']
            
            # --- THIS IS THE FIX ---
            # We now build the schema from the CLEANED data, not the original parsed data.
            # This ensures schema types (e.g., number) match the DB (e.g., number).
            records_to_infer_from = fragment.get('cleaned_records', [])
            # --- END FIX ---

            if not records_to_infer_from:
                # Fallback just in case 'cleaned_records' isn't present, but 'parsed_data' is
                parsed_data = fragment.get('parsed_data', [])
                if isinstance(parsed_data, list):
                    records_to_infer_from = parsed_data
                elif isinstance(parsed_data, dict):
                    records_to_infer_from = [parsed_data]
                else:
                    continue # No data to infer from

            # Create collection name
            collection_name = f"{frag_type}_data"
            
            # Infer field types
            fields_schema = self._infer_fields_schema(records_to_infer_from)
            
            if collection_name in collections:
                # Merge with existing collection schema
                collections[collection_name]['fields'] = self._merge_field_schemas(
                    collections[collection_name]['fields'],
                    fields_schema
                )
                collections[collection_name]['record_count'] += len(records_to_infer_from)
            else:
                collections[collection_name] = {
                    "fields": fields_schema,
                    "record_count": len(records_to_infer_from),
                    "source_type": frag_type
                }
        
        return collections
    
    def _infer_fields_schema(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer field types from records."""
        fields = {}
        total_records = len(records)
        
        # Collect all fields and their values
        field_values = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            for key, value in record.items():
                if key not in field_values:
                    field_values[key] = []
                field_values[key].append(value)
        
        # Infer type and requirements for each field
        for field_name, values in field_values.items():
            non_null_values = [v for v in values if v is not None]
            
            if not non_null_values:
                fields[field_name] = {
                    "type": "null",
                    "required": False,
                    "sample": None
                }
                continue
            
            # Infer type from non-null values
            field_type = self._infer_type(non_null_values)
      
            # Check if all values of this field are present
            is_required = len(values) == total_records
            
            # Check if all *records* have this field
            field_present_in_all_records = len(values) == total_records
            # This logic might need refinement: a field is required if it exists
            # in every record *that belongs to this type*.
            # The current logic is simpler: is it present in all records *in this batch*?
            
            fields[field_name] = {
                "type": field_type,
                "required": field_present_in_all_records,
                "sample": non_null_values[0] if non_null_values else None
            }
        
        return fields
    
    def _infer_type(self, values: List[Any]) -> str:
        """Infer type from list of values."""
        if not values:
            return "unknown"
        
        # Check first non-null value
        types_present = set(type(v) for v in values)
        
        if len(types_present) > 1:
             # Handle mixed lists, e.g., [1, "2.5"]
            if str in types_present or float in types_present or int in types_present:
                return "string" # Default to string if mixed
            return "mixed"
        
        sample = values[0]
        
        if isinstance(sample, bool):
            return "boolean"
        elif isinstance(sample, int):
            return "integer"
        elif isinstance(sample, float):
            return "float"
        elif isinstance(sample, str):
            return "string"
        elif isinstance(sample, list):
            return "array"
        elif isinstance(sample, dict):
            return "object"
        else:
            return "unknown"
    
    def _merge_field_schemas(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two field schemas."""
        merged = existing.copy()
        
        for field_name, field_info in new.items():
            if field_name in merged:
                # Update type if different
                # If one is string, the merged type should be string
                if 'string' in (merged[field_name]['type'], field_info['type']):
                    merged[field_name]['type'] = 'string'
                elif merged[field_name]['type'] != field_info['type']:
                    merged[field_name]['type'] = 'mixed' # e.g., int and float
                
                # Update required status (field is required only if always present)
                merged[field_name]['required'] = merged[field_name]['required'] and field_info['required']
                
                # Update sample
                merged[field_name]['sample'] = field_info['sample']
            else:
                # This is a new field, it's not required for *all* records
                field_info['required'] = False
                merged[field_name] = field_info
        
        return merged
    
    def _merge_schemas(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge existing schema with new schema."""
        merged = existing.copy()
        
        for collection_name, collection_info in new.items():
            if collection_name in merged:
                # Merge field schemas
                merged[collection_name]['fields'] = self._merge_field_schemas(
                    merged[collection_name]['fields'],
                    collection_info['fields']
                )
                # We need to be careful with record counts.
                # This simple add is correct for *new* data.
                merged[collection_name]['record_count'] += collection_info['record_count']
            else:
                merged[collection_name] = collection_info
        
        return merged
    
    async def get_schema(self, source_id: str) -> Dict[str, Any]:
        """Get CURRENT schema for a source."""
        schema = await self.schemas_collection.find_one(
            {"source_id": source_id},
            {"_id": 0}
        )
        return schema
    
    async def get_schema_history(self, source_id: str) -> List[Dict[str, Any]]:
        """NEW: Get all schema versions for a source."""
        history = await self.schema_history_collection.find(
            {"source_id": source_id},
            {"_id": 0}
        ).sort("version", -1).to_list(100) # Sort by version descending
        return history