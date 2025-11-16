"""Data cleaner for field canonicalization and deduplication."""
import logging
from typing import List, Dict, Any, Set
import re

logger = logging.getLogger(__name__)

class DataCleaner:
    """Clean and canonicalize extracted data."""
    
    @staticmethod
    def clean_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and canonicalize records.
        
        Operations:
        - Normalize field names (lowercase, remove special chars)
        - Trim whitespace
        - Deduplicate records
        - Type inference and conversion
        """
        if not records:
            return []
        
        # Normalize field names in all records
        normalized_records = []
        for record in records:
            normalized_record = {}
            for key, value in record.items():
                clean_key = DataCleaner._normalize_field_name(key)
                clean_value = DataCleaner._clean_value(value)
                normalized_record[clean_key] = clean_value
            normalized_records.append(normalized_record)
        
        # Deduplicate records
        deduplicated = DataCleaner._deduplicate_records(normalized_records)
        
        logger.info(f"Cleaned {len(records)} records -> {len(deduplicated)} unique records")
        return deduplicated
    
    @staticmethod
    def _normalize_field_name(field_name: str) -> str:
        """Normalize field name to lowercase snake_case."""
        # Convert to lowercase
        normalized = field_name.lower()
        # Replace spaces and special characters with underscore
        normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        # Collapse multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        return normalized or 'field'
    
    @staticmethod
    def _clean_value(value: Any) -> Any:
        """Clean and infer type for a value."""
        if value is None:
            return None
        
        # Handle strings
        if isinstance(value, str):
            value = value.strip()
            
            # --- START FIX: Robust Numeric Conversion ---
            # Try to convert to float first. This handles "4", "4.0", and "4.5"
            try:
                # Don't convert empty strings to 0
                if value == "":
                    return None
                
                f_value = float(value)
                # If it's a whole number, return as int (e.g., 4.0 -> 4)
                if f_value.is_integer():
                    return int(f_value)
                # Otherwise, return the float
                return f_value
            except (ValueError, TypeError):
                # Not a float, continue...
                pass
            # --- END FIX ---
            
            # Try boolean
            if value.lower() in ['true', 'yes', 'y']:
                return True
            if value.lower() in ['false', 'no', 'n']:
                return False
            
            # Return cleaned string
            return value if value else None
        
        # Handle lists
        if isinstance(value, list):
            return [DataCleaner._clean_value(v) for v in value]
        
        # Handle dicts
        if isinstance(value, dict):
            return {k: DataCleaner._clean_value(v) for k, v in value.items()}
        
        return value
    
    @staticmethod
    def _deduplicate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate records."""
        seen = set()
        unique_records = []
        
        for record in records:
            # Create a hashable representation
            try:
                # Convert to JSON string for hashing (handles nested structures)
                import json
                record_key = json.dumps(record, sort_keys=True, default=str)
                if record_key not in seen:
                    seen.add(record_key)
                    unique_records.append(record)
            except (TypeError, ValueError):
                # If we can't hash it, just add it
                unique_records.append(record)
        
        return unique_records
    
    @staticmethod
    def infer_common_fields(records: List[Dict[str, Any]]) -> Set[str]:
        """Infer common fields across all records."""
        if not records:
            return set()
        
        # Get all field names
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())
        
        return all_fields