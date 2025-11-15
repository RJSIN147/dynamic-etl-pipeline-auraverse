"""Data extractor for identifying and extracting HTML, JSON, and CSV from text."""
import json
import csv
import io
import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extract structured data from mixed-format text."""
    
    def __init__(self, use_slm: bool = False):
        self.use_slm = use_slm
        self.ollama_client = OllamaClient() if use_slm else None
    
    def extract_all_fragments(self, text: str, source_id: str) -> List[Dict[str, Any]]:
        """Extract all HTML, JSON, and CSV fragments from text.
        
        Uses hybrid approach: SLM for detection + heuristic parsers for extraction.
        """
        fragments = []
        
        # First, try SLM-based detection if enabled
        if self.use_slm and self.ollama_client:
            try:
                slm_result = self.ollama_client.extract_structured_data(text[:5000])  # Limit for performance
                logger.info(f"SLM detected fragments: {slm_result}")
            except Exception as e:
                logger.warning(f"SLM detection failed, falling back to heuristics: {e}")
        
        # Use heuristic parsers for reliable extraction
        fragments.extend(self._extract_json_fragments(text))
        fragments.extend(self._extract_html_fragments(text))
        fragments.extend(self._extract_csv_fragments(text))
        
        # Deduplicate and sort by position
        fragments = self._deduplicate_fragments(fragments)
        
        return fragments
    
    def _extract_json_fragments(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON fragments using heuristic parsing."""
        fragments = []
        lines = text.split('\n')
        
        # Find JSON objects and arrays
        in_json = False
        json_start = -1
        brace_count = 0
        bracket_count = 0
        current_json = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Count braces and brackets
            for char in stripped:
                if char == '{':
                    if not in_json:
                        in_json = True
                        json_start = i
                        current_json = []
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    if not in_json and stripped.startswith('['):
                        in_json = True
                        json_start = i
                        current_json = []
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
            
            if in_json:
                current_json.append(line)
                
                # Check if JSON is complete
                if brace_count == 0 and bracket_count == 0:
                    json_text = '\n'.join(current_json)
                    try:
                        # Validate JSON
                        parsed = json.loads(json_text)
                        fragments.append({
                            "type": "json",
                            "start_line": json_start + 1,
                            "end_line": i + 1,
                            "content": json_text,
                            "parsed_data": parsed
                        })
                    except json.JSONDecodeError:
                        # Try to fix common issues
                        try:
                            # Remove trailing commas
                            fixed_json = re.sub(r',\s*(}|])', r'\1', json_text)
                            parsed = json.loads(fixed_json)
                            fragments.append({
                                "type": "json",
                                "start_line": json_start + 1,
                                "end_line": i + 1,
                                "content": fixed_json,
                                "parsed_data": parsed,
                                "note": "malformed_fixed"
                            })
                        except:
                            pass
                    
                    in_json = False
                    json_start = -1
                    current_json = []
        
        return fragments
    
    def _extract_html_fragments(self, text: str) -> List[Dict[str, Any]]:
        """Extract HTML fragments using BeautifulSoup."""
        fragments = []
        lines = text.split('\n')
        
        # Find HTML tags
        html_pattern = re.compile(r'<[^>]+>')
        in_html = False
        html_start = -1
        current_html = []
        
        for i, line in enumerate(lines):
            if html_pattern.search(line):
                if not in_html:
                    in_html = True
                    html_start = i
                    current_html = []
                current_html.append(line)
            elif in_html and line.strip() == '':
                continue
            elif in_html:
                # End of HTML block
                html_text = '\n'.join(current_html)
                try:
                    soup = BeautifulSoup(html_text, 'html.parser')
                    # Parse HTML tables to structured data
                    parsed_data = self._parse_html_tables(soup)
                    if parsed_data or soup.get_text(strip=True):
                        fragments.append({
                            "type": "html",
                            "start_line": html_start + 1,
                            "end_line": i,
                            "content": html_text,
                            "parsed_data": parsed_data
                        })
                except Exception as e:
                    logger.warning(f"Error parsing HTML: {e}")
                
                in_html = False
                html_start = -1
                current_html = []
        
        # Handle end of file
        if in_html and current_html:
            html_text = '\n'.join(current_html)
            try:
                soup = BeautifulSoup(html_text, 'html.parser')
                parsed_data = self._parse_html_tables(soup)
                fragments.append({
                    "type": "html",
                    "start_line": html_start + 1,
                    "end_line": len(lines),
                    "content": html_text,
                    "parsed_data": parsed_data
                })
            except Exception as e:
                logger.warning(f"Error parsing HTML: {e}")
        
        return fragments
    
    def _parse_html_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract structured data from HTML tables."""
        tables_data = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = []
            headers = []
            
            # Extract headers
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Extract rows
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    if headers:
                        row_dict = dict(zip(headers, cells))
                        rows.append(row_dict)
                    else:
                        rows.append(cells)
            
            if rows:
                tables_data.append({"table": rows})
        
        return tables_data
    
    def _extract_csv_fragments(self, text: str) -> List[Dict[str, Any]]:
        """Extract CSV fragments using heuristic detection."""
        fragments = []
        lines = text.split('\n')
        
        in_csv = False
        csv_start = -1
        current_csv = []
        delimiter = ','
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip lines that are clearly JSON
            if stripped.startswith(('{', '[', '}', ']')) or ':' in stripped and '{' in stripped:
                if in_csv and current_csv:
                    # End CSV block
                    csv_text = '\n'.join(current_csv)
                    parsed = self._parse_csv(csv_text, delimiter)
                    if parsed and len(parsed) >= 2:  # Need at least 2 rows for valid CSV
                        fragments.append({
                            "type": "csv",
                            "start_line": csv_start + 1,
                            "end_line": i,
                            "content": csv_text,
                            "parsed_data": parsed,
                            "delimiter": delimiter
                        })
                    in_csv = False
                    csv_start = -1
                    current_csv = []
                continue
            
            # Detect CSV by checking for consistent delimiters
            if not in_csv and stripped:
                for delim in [',', ';', '\t', '|']:
                    if delim in stripped and len(stripped.split(delim)) >= 2:
                        # Check if it looks like CSV (not JSON)
                        if ':' not in stripped or delim != ',':
                            in_csv = True
                            csv_start = i
                            current_csv = [line]
                            delimiter = delim
                            break
            elif in_csv:
                # Check if line continues CSV pattern
                if (delimiter in stripped and len(stripped.split(delimiter)) >= 2) or stripped == '':
                    current_csv.append(line)
                else:
                    # End of CSV
                    csv_text = '\n'.join(current_csv)
                    parsed = self._parse_csv(csv_text, delimiter)
                    if parsed and len(parsed) >= 2:  # Need at least 2 rows
                        fragments.append({
                            "type": "csv",
                            "start_line": csv_start + 1,
                            "end_line": i,
                            "content": csv_text,
                            "parsed_data": parsed,
                            "delimiter": delimiter
                        })
                    
                    in_csv = False
                    csv_start = -1
                    current_csv = []
        
        # Handle end of file
        if in_csv and current_csv:
            csv_text = '\n'.join(current_csv)
            parsed = self._parse_csv(csv_text, delimiter)
            if parsed and len(parsed) >= 2:
                fragments.append({
                    "type": "csv",
                    "start_line": csv_start + 1,
                    "end_line": len(lines),
                    "content": csv_text,
                    "parsed_data": parsed,
                    "delimiter": delimiter
                })
        
        return fragments
    
    def _parse_csv(self, csv_text: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Parse CSV text to structured data."""
        try:
            reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
            return [row for row in reader]
        except Exception as e:
            logger.warning(f"Error parsing CSV: {e}")
            # Try without headers
            try:
                reader = csv.reader(io.StringIO(csv_text), delimiter=delimiter)
                rows = [row for row in reader]
                if len(rows) > 1:
                    headers = rows[0]
                    return [dict(zip(headers, row)) for row in rows[1:]]
            except:
                pass
            return []
    
    def _deduplicate_fragments(self, fragments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or overlapping fragments."""
        if not fragments:
            return []
        
        # Sort by start line
        fragments.sort(key=lambda x: x['start_line'])
        
        # Remove duplicates based on type and line range
        seen = set()
        unique_fragments = []
        
        for frag in fragments:
            key = (frag['type'], frag['start_line'], frag['end_line'])
            if key not in seen:
                seen.add(key)
                unique_fragments.append(frag)
        
        return unique_fragments
