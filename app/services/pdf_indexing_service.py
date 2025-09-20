"""
PDF Document Indexing Service
Handles indexing and searching of pharmacy documents from the GyaniNuxeo folder
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import json
from datetime import datetime
import PyPDF2
from docx import Document
import re

logger = logging.getLogger(__name__)

class PDFIndexingService:
    """Service for indexing and searching pharmacy PDF documents"""
    
    def __init__(self, documents_folder: str = "GyaniNuxeo"):
        self.documents_folder = documents_folder
        self.index_file = "document_index.json"
        self.documents_index: Dict[str, Any] = {}
        self.supported_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        
    def initialize(self) -> bool:
        """Initialize the PDF indexing service"""
        try:
            self.load_index()
            self.scan_documents()
            logger.info("PDF indexing service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PDF indexing service: {e}")
            return False
    
    def load_index(self) -> None:
        """Load existing document index from file"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.documents_index = json.load(f)
                logger.info(f"Loaded {len(self.documents_index)} documents from index")
            else:
                self.documents_index = {}
                logger.info("No existing index found, starting with empty index")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self.documents_index = {}
    
    def save_index(self) -> None:
        """Save document index to file"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents_index, f, indent=2, default=str)
            logger.info(f"Saved index with {len(self.documents_index)} documents")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def scan_documents(self) -> None:
        """Scan the documents folder and update index"""
        if not os.path.exists(self.documents_folder):
            logger.warning(f"Documents folder '{self.documents_folder}' not found")
            return
        
        try:
            document_files = []
            for root, dirs, files in os.walk(self.documents_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = Path(file).suffix.lower()
                    
                    if file_ext in self.supported_extensions:
                        document_files.append(file_path)
            
            logger.info(f"Found {len(document_files)} supported documents")
            
            # Index each document
            for file_path in document_files:
                self.index_document(file_path)
            
            self.save_index()
            
        except Exception as e:
            logger.error(f"Error scanning documents: {e}")
    
    def index_document(self, file_path: str) -> None:
        """Index a single document"""
        try:
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Create file hash for change detection
            file_hash = self.get_file_hash(file_path)
            
            # Check if document is already indexed and unchanged
            relative_path = os.path.relpath(file_path)
            if relative_path in self.documents_index:
                existing_doc = self.documents_index[relative_path]
                if existing_doc.get('file_hash') == file_hash:
                    return  # Document unchanged, skip indexing
            
            # Extract document metadata
            filename = os.path.basename(file_path)
            file_ext = Path(file_path).suffix.lower()
            
            # Extract text content from the document
            extracted_text = self.extract_text_from_file(file_path, file_ext)
            
            # Create document entry
            doc_entry = {
                'filename': filename,
                'filepath': relative_path,
                'full_path': os.path.abspath(file_path),
                'file_extension': file_ext,
                'file_size': file_size,
                'modified_time': modified_time,
                'file_hash': file_hash,
                'indexed_time': datetime.now(),
                'title': self.extract_title_from_filename(filename),
                'category': self.categorize_document(filename),
                'keywords': self.extract_keywords_from_filename(filename),
                'text_content': extracted_text[:2000] if extracted_text else '',  # Store first 2000 chars
                'full_text': extracted_text  # Store full text for search
            }
            
            # Create searchable text combining metadata and content
            doc_entry['searchable_text'] = self.create_searchable_text(doc_entry)
            
            self.documents_index[relative_path] = doc_entry
            logger.debug(f"Indexed document: {filename} ({len(extracted_text) if extracted_text else 0} characters)")
            
        except Exception as e:
            logger.error(f"Error indexing document {file_path}: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Generate hash for file to detect changes"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read first 1KB and last 1KB for speed
                hasher.update(f.read(1024))
                f.seek(-1024, 2)
                hasher.update(f.read(1024))
            return hasher.hexdigest()
        except Exception:
            # Fallback to file size and modified time
            stat = os.stat(file_path)
            return hashlib.md5(f"{stat.st_size}_{stat.st_mtime}".encode()).hexdigest()
    
    def extract_text_from_file(self, file_path: str, file_ext: str) -> str:
        """Extract text content from different file types"""
        try:
            if file_ext == '.pdf':
                return self.extract_text_from_pdf(file_path)
            elif file_ext == '.docx':
                return self.extract_text_from_docx(file_path)
            elif file_ext == '.doc':
                # For .doc files, we'll try to read as text (limited support)
                return self.extract_text_from_doc(file_path)
            elif file_ext == '.txt':
                return self.extract_text_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file type for text extraction: {file_ext}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page in {file_path}: {e}")
                        continue
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_doc(self, file_path: str) -> str:
        """Extract text from DOC files (limited support)"""
        try:
            # For .doc files, we'll try to read as binary and extract readable text
            # This is a basic approach and may not work for all .doc files
            with open(file_path, 'rb') as file:
                content = file.read()
                # Try to extract readable ASCII text
                text = re.sub(rb'[^\x20-\x7E\n\r\t]', b' ', content).decode('ascii', errors='ignore')
                # Clean up multiple spaces and newlines
                text = re.sub(r'\s+', ' ', text).strip()
                return text
        except Exception as e:
            logger.error(f"Error reading DOC {file_path}: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {e}")
            return ""
    
    def extract_title_from_filename(self, filename: str) -> str:
        """Extract a readable title from filename"""
        # Remove extension
        title = os.path.splitext(filename)[0]
        
        # Clean up common patterns
        title = title.replace('_', ' ').replace('-', ' ')
        
        # Remove common prefixes/patterns
        if title.startswith('MED D '):
            title = title[6:]
        elif title.startswith('MEDD '):
            title = title[5:]
        
        return title.strip()
    
    def categorize_document(self, filename: str) -> str:
        """Categorize document based on filename"""
        filename_lower = filename.lower()
        
        if 'med d' in filename_lower or 'medd' in filename_lower:
            return 'Medicare Part D'
        elif 'compass' in filename_lower:
            return 'Compass System'
        elif 'peoplesafe' in filename_lower:
            return 'PeopleSafe System'
        elif 'caremark.com' in filename_lower:
            return 'Caremark Website'
        elif 'prior authorization' in filename_lower or ' pa ' in filename_lower:
            return 'Prior Authorization'
        elif 'formulary' in filename_lower:
            return 'Formulary'
        elif 'recall' in filename_lower:
            return 'Drug Recall'
        elif 'test claim' in filename_lower:
            return 'Test Claims'
        elif 'specialty' in filename_lower:
            return 'Specialty Pharmacy'
        elif 'mail order' in filename_lower or 'home delivery' in filename_lower:
            return 'Mail Order'
        elif 'billing' in filename_lower or 'payment' in filename_lower:
            return 'Billing & Payments'
        else:
            return 'General'
    
    def extract_keywords_from_filename(self, filename: str) -> List[str]:
        """Extract keywords from filename for search"""
        keywords = []
        filename_lower = filename.lower()
        
        # Common pharmacy terms
        pharmacy_terms = [
            'prescription', 'rx', 'medication', 'drug', 'formulary', 'prior authorization',
            'test claim', 'specialty', 'mail order', 'medicare', 'billing', 'payment',
            'compass', 'peoplesafe', 'caremark', 'recall', 'override', 'rejection',
            'coverage', 'benefit', 'enrollment', 'member', 'copay', 'deductible',
            'cvs', 'pharmacy', 'pharmacist', 'insulin', 'diabetic', 'vaccine',
            'opioid', 'controlled substance', 'generic', 'brand', 'dosage', 'refill',
            'claims', 'rebate', 'tier', 'step therapy', 'quantity limit', 'PA',
            'auth', 'approval', 'denial', 'appeal', 'grievance', 'complaint'
        ]
        
        for term in pharmacy_terms:
            if term in filename_lower:
                keywords.append(term)
        
        # Extract ID numbers
        import re
        ids = re.findall(r'\d{5,}', filename)
        keywords.extend(ids)
        
        return list(set(keywords))  # Remove duplicates
    
    def create_searchable_text(self, doc_entry: Dict[str, Any]) -> str:
        """Create searchable text from document metadata and content"""
        searchable_parts = [
            doc_entry['title'],
            doc_entry['filename'],
            doc_entry['category'],
            ' '.join(doc_entry['keywords']),
            doc_entry.get('full_text', '')  # Include extracted text content
        ]
        
        return ' '.join(filter(None, searchable_parts)).lower()
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents based on query"""
        if not query.strip():
            return []
        
        query_lower = query.lower()
        results = []
        
        for doc_path, doc_info in self.documents_index.items():
            score = self.calculate_relevance_score(query_lower, doc_info)
            if score > 0:
                result = doc_info.copy()
                result['relevance_score'] = score
                result['document_link'] = f"/documents/{doc_path}"
                
                # Extract relevant snippet from text content
                snippet = self.extract_relevant_snippet(query_lower, doc_info.get('full_text', ''))
                if snippet:
                    result['snippet'] = snippet
                else:
                    # Fallback to title or filename-based description
                    result['snippet'] = f"Document about {doc_info.get('title', doc_info.get('filename', ''))}"
                
                # Remove full_text from result to save space
                result.pop('full_text', None)
                
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results[:limit]
    
    def extract_relevant_snippet(self, query: str, text: str, snippet_length: int = 200) -> str:
        """Extract a relevant snippet from text based on query"""
        if not text or not query:
            return ""
        
        text_lower = text.lower()
        
        # Find the best match position
        best_pos = -1
        best_score = 0
        
        # Try to find exact phrase match first
        if query in text_lower:
            best_pos = text_lower.find(query)
            best_score = 10
        else:
            # Look for individual words
            query_words = query.split()
            for word in query_words:
                if word in text_lower:
                    pos = text_lower.find(word)
                    if pos >= 0 and best_score < 5:
                        best_pos = pos
                        best_score = 5
        
        if best_pos >= 0:
            # Extract snippet around the match
            start = max(0, best_pos - snippet_length // 2)
            end = min(len(text), best_pos + snippet_length // 2)
            
            snippet = text[start:end].strip()
            
            # Try to start and end at word boundaries
            if start > 0:
                first_space = snippet.find(' ')
                if first_space > 0:
                    snippet = snippet[first_space:].strip()
            
            if end < len(text):
                last_space = snippet.rfind(' ')
                if last_space > 0:
                    snippet = snippet[:last_space].strip()
            
            # Add ellipsis if needed
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            
            return snippet
        
        # Fallback: return beginning of text
        return text[:snippet_length].strip() + ("..." if len(text) > snippet_length else "")
    
    def calculate_relevance_score(self, query: str, doc_info: Dict[str, Any]) -> float:
        """Calculate relevance score for a document"""
        score = 0.0
        
        searchable_text = doc_info.get('searchable_text', '').lower()
        title = doc_info.get('title', '').lower()
        filename = doc_info.get('filename', '').lower()
        full_text = doc_info.get('full_text', '').lower()
        
        # Exact phrase match in title (highest score)
        if query in title:
            score += 20.0
        
        # Exact phrase match in filename
        if query in filename:
            score += 15.0
        
        # Exact phrase match in document content
        if query in full_text:
            score += 10.0
            # Count multiple occurrences in content
            occurrences = full_text.count(query)
            score += min(occurrences * 2.0, 10.0)  # Bonus for multiple matches, max 10
        
        # Exact phrase match in searchable text
        if query in searchable_text:
            score += 5.0
        
        # Individual word matches
        query_words = query.split()
        for word in query_words:
            if len(word) < 3:  # Skip very short words
                continue
                
            if word in title:
                score += 5.0
            elif word in filename:
                score += 3.0
            elif word in full_text:
                # Count word frequency in content
                word_count = full_text.count(word)
                score += min(word_count * 0.5, 5.0)  # Bonus for word frequency, max 5
            elif word in searchable_text:
                score += 1.0
        
        return score
    
    def get_document_info(self, document_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific document"""
        return self.documents_index.get(document_path)
    
    def get_categories(self) -> List[str]:
        """Get all document categories"""
        categories = set()
        for doc_info in self.documents_index.values():
            categories.add(doc_info.get('category', 'General'))
        return sorted(list(categories))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        total_docs = len(self.documents_index)
        categories = {}
        
        for doc_info in self.documents_index.values():
            category = doc_info.get('category', 'General')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_documents': total_docs,
            'categories': categories,
            'documents_folder': self.documents_folder,
            'last_scan': datetime.now().isoformat()
        }


# Global instance
pdf_indexing_service = None

def get_pdf_indexing_service() -> PDFIndexingService:
    """Get the global PDF indexing service instance"""
    global pdf_indexing_service
    if pdf_indexing_service is None:
        pdf_indexing_service = PDFIndexingService()
        pdf_indexing_service.initialize()
    return pdf_indexing_service
