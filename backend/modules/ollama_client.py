# """Ollama client for LLM and SLM operations."""
# import ollama
# import json
# import logging
# from typing import Dict, Any, Optional

# logger = logging.getLogger(__name__)

# class OllamaClient:
#     """Client for interacting with Ollama models."""
    
#     def __init__(self, model: str = "qwen2.5:0.5b"):
#         self.model = model
#         self.client = ollama
        
#     def generate(self, prompt: str, system: Optional[str] = None) -> str:
#         """Generate text using Ollama model."""
#         try:
#             messages = []
#             if system:
#                 messages.append({"role": "system", "content": system})
#             messages.append({"role": "user", "content": prompt})
            
#             response = self.client.chat(
#                 model=self.model,
#                 messages=messages
#             )
#             return response['message']['content']
#         except Exception as e:
#             logger.error(f"Ollama generation error: {e}")
#             raise
    
#     def extract_structured_data(self, text: str) -> Dict[str, Any]:
#         """Extract structured data types from text using SLM."""
#         system_prompt = """You are a data type detector. Analyze the given text and identify segments that contain HTML, JSON, or CSV data.
# Return a JSON object with this structure:
# {
#   "fragments": [
#     {"type": "html"|"json"|"csv", "start_line": number, "end_line": number, "content": "snippet"},
#     ...
#   ]
# }
# Be precise with line numbers and data type identification."""
        
#         user_prompt = f"""Analyze this text and identify all HTML, JSON, and CSV fragments:

# {text}

# Return only valid JSON."""
        
#         try:
#             response = self.generate(user_prompt, system_prompt)
#             # Clean response to extract JSON
#             response = response.strip()
#             if "```json" in response:
#                 response = response.split("```json")[1].split("```")[0].strip()
#             elif "```" in response:
#                 response = response.split("```")[1].split("```")[0].strip()
            
#             return json.loads(response)
#         except json.JSONDecodeError:
#             logger.warning("SLM returned invalid JSON, using fallback")
#             return {"fragments": []}
#         except Exception as e:
#             logger.error(f"Error extracting structured data: {e}")
#             return {"fragments": []}
    
# #     def translate_nl_to_query(self, natural_language: str, schema: Dict[str, Any]) -> str:
# #         """Translate natural language to MongoDB query."""
# #         system_prompt = """You are a MongoDB query expert. Convert natural language questions to MongoDB queries.
# # Given a schema and a question, return a valid MongoDB query as a JSON object.
# # For find operations, return: {"operation": "find", "filter": {...}, "projection": {...}}
# # For aggregate operations, return: {"operation": "aggregate", "pipeline": [...]}
# # Return only valid JSON, no explanations."""
        
# #         user_prompt = f"""Schema: {json.dumps(schema, indent=2)}

# # Question: {natural_language}

# # Generate MongoDB query:"""
        
# #         try:
# #             response = self.generate(user_prompt, system_prompt)
# #             # Clean response
# #             response = response.strip()
# #             if "```json" in response:
# #                 response = response.split("```json")[1].split("```")[0].strip()
# #             elif "```" in response:
# #                 response = response.split("```")[1].split("```")[0].strip()
            
# #             return response
# #         except Exception as e:
# #             logger.error(f"Error translating NL to query: {e}")
# #             raise
#     def translate_nl_to_query(self, natural_language: str, schema: Dict[str, Any]) -> str:
#         """Translate natural language to MongoDB query."""
        
#         # This new system prompt is much stricter and gives examples.
#         system_prompt = """You are a MongoDB query expert. Your task is to convert a user's natural language question into a valid MongoDB query, based on a provided schema.
        
# You MUST adhere to the following rules:
# 1.  Return **ONLY** a single, valid, RFC 8259-compliant JSON object.
# 2.  All keys and all string values **MUST** be enclosed in **double quotes**.
# 3.  Do not include any explanations, markdown (like ```json), or any text outside of the JSON object.
# 4.  Use the provided schema to determine field names and data types.
# 5.  For simple "find" operations, use:
#     `{"operation": "find", "filter": {...}, "projection": {"_id": 0}}`
# 6.  For "aggregate" operations, use:
#     `{"operation": "aggregate", "pipeline": [...]}`
# 7.  Always include `"projection": {"_id": 0}` in "find" operations.
# """
        
#         # This new user prompt clearly separates the schema from the question.
#         user_prompt = f"""Here is the schema:
# {json.dumps(schema, indent=2)}

# Here is the user's question:
# "{natural_language}"

# Generate the MongoDB query JSON now.
# """
        
#         try:
#             response = self.generate(user_prompt, system_prompt)
#             # Clean response (this is still a good fallback)
#             response = response.strip()
#             if "```json" in response:
#                 response = response.split("```json")[1].split("```")[0].strip()
#             elif "```" in response:
#                 response = response.split("```")[1].split("```")[0].strip()
            
#             # Remove potential newlines or extra text just in case
#             response = response[response.find('{'):response.rfind('}')+1]

#             return response
#         except Exception as e:
#             logger.error(f"Error translating NL to query: {e}")
#             raise
"""Ollama client for LLM and SLM operations."""
import ollama
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama models."""
    
    def __init__(self, model: str = "llama3:8b"):
        self.model = model
        self.client = ollama
        
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate text using Ollama model."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data types from text using SLM."""
        system_prompt = """You are a data type detector. Analyze the given text and identify segments that contain HTML, JSON, or CSV data.
Return a JSON object with this structure:
{
  "fragments": [
    {"type": "html"|"json"|"csv", "start_line": number, "end_line": number, "content": "snippet"},
    ...
  ]
}
Be precise with line numbers and data type identification."""
        
        user_prompt = f"""Analyze this text and identify all HTML, JSON, and CSV fragments:

{text}

Return only valid JSON."""
        
        try:
            response = self.generate(user_prompt, system_prompt)
            # Clean response to extract JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("SLM returned invalid JSON, using fallback")
            return {"fragments": []}
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {"fragments": []}
    
    def translate_nl_to_query(self, natural_language: str, schema: Dict[str, Any]) -> str:
        """Translate natural language to MongoDB query."""
        
        # <-- MODIFIED PROMPT START -->
        # This new system prompt is much stricter and gives "GOOD" vs "BAD" examples
        # to prevent the LLM from using incorrect syntax like $expr for simple queries.
        system_prompt = """You are a MongoDB query expert. Your task is to convert a user's natural language question into a valid MongoDB query, based on a provided schema.
        
You MUST adhere to the following rules:
1.  Return **ONLY** a single, valid, RFC 8259-compliant JSON object.
2.  All keys and all string values **MUST** be enclosed in **double quotes**.
3.  Do not include any explanations, markdown (like ```json), or any text outside of the JSON object.
4.  Use the provided schema to determine field names and data types.
5.  For simple comparisons (e.g., greater than, less than, equals), use standard MongoDB query operators, **NOT** `$expr`.
    -   **Query:** "show me products where price is greater than 100"
    -   **GOOD:** `{"operation": "find", "filter": {"price": {"$gt": 100}}, "projection": {"_id": 0}}`
    -   **BAD:** `{"operation": "find", "filter": {"$expr": {"$gt": ["$price", 100]}}}`
6.  For "aggregate" operations, use:
    `{"operation": "aggregate", "pipeline": [...]}`
7.  Always include `"projection": {"_id": 0}` in "find" operations.
"""
        
        # This new user prompt clearly separates the schema from the question.
        user_prompt = f"""Here is the schema:
{json.dumps(schema, indent=2)}

Here is the user's question:
"{natural_language}"

Generate the MongoDB query JSON now.
"""
        # <-- MODIFIED PROMPT END -->

        try:
            response = self.generate(user_prompt, system_prompt)
            
            # <-- MODIFIED CLEANING LOGIC START -->
            # Clean response (this is still a good fallback)
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # Force extract the JSON object, just in case the LLM still adds text
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                response = response[start:end+1]
            # <-- MODIFIED CLEANING LOGIC END -->
            
            return response
        except Exception as e:
            logger.error(f"Error translating NL to query: {e}")
            raise