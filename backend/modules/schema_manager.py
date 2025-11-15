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
    
    async def generate_schema(self, source_id: str, fragments: List[Dict[str, Any]], 
                             all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate database-agnostic schema from extracted data.
        
        Schema structure:
        {
            "source_id": str,
            "version": int,
            "created_at": datetime,
            "updated_at": datetime,
            "collections": {
                "collection_name": {
                    "fields": {
                        "field_name": {"type": str, "required": bool, "sample": Any}
                    },
                    "record_count": int
                }
            },
            "data_types_present": ["html", "json", "csv"]
        }
        """
        # Get existing schema if any
        existing_schema = await self.schemas_collection.find_one(
            {"source_id": source_id},
            {"_id": 0}
        )
        
        # Infer schema from records
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
        
        # Save schema
        await self.schemas_collection.update_one(
            {"source_id": source_id},
            {"$set": schema},
            upsert=True
        )
        
        logger.info(f"Schema generated for source_id={source_id}, version={schema['version']}")
        return schema
    
    def _infer_collections_schema(self, fragments: List[Dict[str, Any]], 
                                 all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer schema for collections based on data fragments."""
        collections = {}
        
        # Group records by fragment type
        for fragment in fragments:
            frag_type = fragment['type']
            parsed_data = fragment.get('parsed_data', [])
            
            if not parsed_data:
                continue
            
            # Handle different data structures
            if isinstance(parsed_data, list):
                records = parsed_data
            elif isinstance(parsed_data, dict):
                records = [parsed_data]
            else:
                continue
            
            # Create collection name
            collection_name = f"{frag_type}_data"
            
            # Infer field types
            fields_schema = self._infer_fields_schema(records)
            
            if collection_name in collections:
                # Merge with existing collection schema
                collections[collection_name]['fields'] = self._merge_field_schemas(
                    collections[collection_name]['fields'],
                    fields_schema
                )
                collections[collection_name]['record_count'] += len(records)
            else:
                collections[collection_name] = {
                    "fields": fields_schema,
                    "record_count": len(records),
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
            is_required = len(non_null_values) == total_records
            
            fields[field_name] = {
                "type": field_type,
                "required": is_required,
                "sample": non_null_values[0] if non_null_values else None
            }
        
        return fields
    
    def _infer_type(self, values: List[Any]) -> str:
        """Infer type from list of values."""
        if not values:
            return "unknown"
        
        # Check first non-null value
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
                # Update type if different (prefer more specific type)
                if merged[field_name]['type'] != field_info['type']:
                    merged[field_name]['type'] = 'mixed'
                # Update required status (field is required only if always present)
                merged[field_name]['required'] = merged[field_name]['required'] and field_info['required']
            else:
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
                merged[collection_name]['record_count'] += collection_info['record_count']
            else:
                merged[collection_name] = collection_info
        
        return merged
    
    async def get_schema(self, source_id: str) -> Dict[str, Any]:
        """Get schema for a source."""
        schema = await self.schemas_collection.find_one(
            {"source_id": source_id},
            {"_id": 0}
        )
        return schema
