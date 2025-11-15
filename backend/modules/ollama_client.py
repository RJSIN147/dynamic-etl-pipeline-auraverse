"""Ollama client for LLM and SLM operations."""
import ollama
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama models."""
    
    def __init__(self, model: str = "qwen2.5:0.5b"):
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
        system_prompt = """You are a MongoDB query expert. Convert natural language questions to MongoDB queries.
Given a schema and a question, return a valid MongoDB query as a JSON object.
For find operations, return: {"operation": "find", "filter": {...}, "projection": {...}}
For aggregate operations, return: {"operation": "aggregate", "pipeline": [...]}
Return only valid JSON, no explanations."""
        
        user_prompt = f"""Schema: {json.dumps(schema, indent=2)}

Question: {natural_language}

Generate MongoDB query:"""
        
        try:
            response = self.generate(user_prompt, system_prompt)
            # Clean response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            return response
        except Exception as e:
            logger.error(f"Error translating NL to query: {e}")
            raise
