"""File parser for extracting content from different file formats."""
import logging
from pathlib import Path
from typing import Tuple
import PyPDF2

logger = logging.getLogger(__name__)

class FileParser:
    """Parser for .txt, .pdf, and .md files."""
    
    @staticmethod
    def parse_file(file_path: str) -> Tuple[str, str]:
        """Parse file and return content and file type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content, file_type)
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            return FileParser._parse_pdf(file_path), 'pdf'
        elif suffix in ['.txt', '.md']:
            return FileParser._parse_text(file_path), suffix[1:]
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    @staticmethod
    def _parse_text(file_path: str) -> str:
        """Parse text or markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """Parse PDF file and extract text."""
        try:
            content = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        content.append(text)
            return '\n'.join(content)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
