"""Data extractor for identifying and extracting HTML, JSON, CSV, and XML from text."""
import json
import csv
import io
import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from lxml import etree # <-- NEW IMPORT
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extract structured data from mixed-format text."""
    
    def __init__(self, use_slm: bool = True):
        self.use_slm = use_slm
        self.ollama_client = OllamaClient() if use_slm else None
    
    def extract_all_fragments(self, text: str, source_id: str) -> List[Dict[str, Any]]:
        """Extract all HTML, JSON, CSV, and XML fragments from text.
        
        Uses hybrid approach: SLM for detection + heuristic parsers for extraction.
        """
        fragments = []
        
        # First, try SLM-based detection if enabled
        if self.use_slm and self.ollama_client:
            try:
                # Limit text for SLM detection for performance
                slm_result = self.ollama_client.extract_structured_data(text[:5000])
                logger.info(f"SLM detected fragments: {slm_result}")
            except Exception as e:
                logger.warning(f"SLM detection failed, falling back to heuristics: {e}")
        
        # Use heuristic parsers for reliable extraction
        fragments.extend(self._extract_json_fragments(text))
        fragments.extend(self._extract_html_fragments(text))
        fragments.extend(self._extract_csv_fragments(text))
        fragments.extend(self._extract_xml_fragments(text)) # <-- NEW CALL
        
        # Deduplicate and sort by position
        fragments = self._deduplicate_fragments(fragments)
        
        return fragments
    
    # Existing _extract_json_fragments... (omitted for brevity, assume content is unchanged)
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
        
    # Existing _extract_html_fragments... (omitted for brevity, assume content is unchanged)
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
    
    # Existing _extract_csv_fragments... (omitted for brevity, assume content is unchanged)
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
            
            # Skip lines that are clearly JSON or XML (new skip for XML)
            if stripped.startswith(('{', '[', '}', ']')) or ':' in stripped and '{' in stripped or stripped.startswith('<') and stripped.endswith('>'):
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
                        # Check if it looks like CSV (not JSON or simple text)
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

    # --- NEW XML EXTRACTION LOGIC ---
    def _xml_to_dict(self, element: etree.Element) -> Dict[str, Any]:
        """Recursively converts an lxml Element to a dictionary."""
        d = dict(element.attrib)
        
        # Get text content if no children
        text = (element.text or '').strip()
        if text:
            d['text_content'] = text

        for child in element:
            child_tag = child.tag
            child_dict = self._xml_to_dict(child)
            
            # Handle list of children with the same tag (e.g., multiple <supplier> tags)
            if child_tag in d:
                if isinstance(d[child_tag], list):
                    d[child_tag].append(child_dict)
                else:
                    d[child_tag] = [d[child_tag], child_dict]
            else:
                d[child_tag] = child_dict
        
        # If the element has children and attributes, combine them with the tag name as a key
        if element.attrib or list(element):
            # If it's a list item (like a supplier), return the contents directly
            if not d.get('text_content'):
                del d['text_content']
            return d
        
        # If only text content, return text content directly (for leaf nodes)
        return text if text else d

    def _extract_xml_fragments(self, text: str) -> List[Dict[str, Any]]:
        """Extract XML fragments using lxml and convert to flat records."""
        fragments = []
        lines = text.split('\n')
        
        # Regex to find XML-like structures (starting with '<?xml' or a root tag)
        xml_pattern = re.compile(r'(<\?xml.*?\?>)?\s*<[a-zA-Z_][^>]*>.*?</[a-zA-Z_][^>]*>', re.DOTALL)
        
        for match in xml_pattern.finditer(text):
            xml_text = match.group(0).strip()
            
            # Determine line numbers (simple heuristic based on char index)
            start_index = match.start()
            end_index = match.end()
            start_line = text[:start_index].count('\n') + 1
            end_line = text[:end_index].count('\n') + 1
            
            try:
                # 1. Parse the XML
                parser = etree.XMLParser(recover=True, encoding='utf-8')
                root = etree.fromstring(xml_text.encode('utf-8'), parser=parser)
                
                # 2. Convert to list of flat records. We assume the children of the
                #    root element are the logical records.
                records = []
                # Use the root tag name to name the collection of records
                collection_tag = root.tag
                
                # Check if the root has relevant children (the actual records)
                if len(root) > 0:
                    for element in root:
                        # Convert each child element into a single flat record dictionary
                        record_dict = self._xml_to_dict(element)
                        
                        # Add attributes of the root element to all records (optional, but useful)
                        for attr, val in root.attrib.items():
                            record_dict[f'root_attr_{attr}'] = val
                            
                        # Flatten the nested dictionary if possible
                        flat_record = self._flatten_dict(record_dict)
                        records.append(flat_record)
                
                if records:
                    fragments.append({
                        "type": "xml",
                        "start_line": start_line,
                        "end_line": end_line,
                        "content": xml_text,
                        # Pass a list of records directly, similar to CSV/JSON array
                        "parsed_data": records
                    })
                    
            except etree.XMLSyntaxError as e:
                logger.warning(f"XML Syntax Error: {e} in fragment starting at line {start_line}")
            except Exception as e:
                logger.error(f"Error processing XML fragment: {e}")

        return fragments

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flattens a nested dictionary, which helps with the XML-to-JSON conversion."""
        items = {}
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                # We stop flattening if a nested dictionary contains a list, 
                # as that represents an array/sub-document which MongoDB handles well.
                has_list_child = any(isinstance(val, list) for val in v.values())
                if has_list_child:
                    items[new_key] = v
                else:
                    items.update(self._flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                # Keep lists as they are (representing multiple elements/sub-records)
                items[new_key] = v
            else:
                items[new_key] = v
        return items
    
    # Existing _deduplicate_fragments... (omitted for brevity, assume content is unchanged)
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