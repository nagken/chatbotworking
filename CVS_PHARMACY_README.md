# CVS Pharmacy Knowledge Assist

A clean, focused implementation of the CVS Pharmacy Knowledge Assist chatbot for pharmacy staff, customer service representatives, and healthcare professionals.

## Features

### ✅ Implemented
1. **Working Server with Login** - Any credentials work for development
2. **PDF Document Indexing** - Automatically indexes documents from GyaniNuxeo folder
3. **Pharmacy-Specific UI** - Updated with CVS branding and pharmacy-focused questions
4. **Thumbs Up/Down Feedback** - Fully functional feedback system for responses
5. **Document Search Integration** - Search results show links to source PDFs
6. **Pre-populated Questions** - Ready-to-use pharmacy queries:
   - "How do I add a credit card to a member's profile?"
   - "How do I access a member's mail order history?"
   - "How do I transfer a prescription from mail to retail?"
   - "How do I submit a test claim for a commercial plan?"

## Quick Start

### Option 1: Using the Startup Script
```bash
# Simply run the startup script
start-cvs-pharmacy.bat
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Access the Application

1. Open your browser to `http://localhost:8080`
2. Login with any credentials (development mode):
   - Email: `admin@cvs-pharmacy-knowledge-assist.com`
   - Password: `admin123`
3. Start asking pharmacy-related questions!

## Document Search

The system automatically indexes documents from the `GyaniNuxeo` folder containing:
- Medicare Part D procedures
- Compass system guides
- PeopleSafe workflows
- Caremark website instructions
- Prior authorization procedures
- Drug recalls and safety information
- Test claim procedures
- Specialty pharmacy guides

### Supported Document Types
- PDF files (`.pdf`)
- Word documents (`.doc`, `.docx`)
- Text files (`.txt`)

## API Endpoints

### Chat
- `POST /api/chat/message` - Send a chat message
- `POST /api/chat/stream` - Stream chat responses

### Documents
- `GET /api/documents/search?q={query}` - Search documents
- `GET /api/documents/download/{file_path}` - Download a document
- `GET /api/documents/stats` - Get indexing statistics
- `GET /api/documents/reindex` - Trigger reindexing

### Feedback
- `POST /api/feedback/submit` - Submit thumbs up/down feedback

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/validate` - Validate session
- `POST /api/auth/logout` - User logout

## Architecture

```
CVS Pharmacy Knowledge Assist
├── Frontend (Static HTML/JS/CSS)
│   ├── Login system with CVS branding
│   ├── Chat interface with pre-populated questions
│   ├── Document search integration
│   └── Feedback system (thumbs up/down)
├── Backend (FastAPI)
│   ├── Authentication routes
│   ├── Chat processing with document search
│   ├── PDF indexing service
│   ├── Feedback collection
│   └── Document serving
└── Document Index
    ├── GyaniNuxeo folder scanning
    ├── Metadata extraction
    ├── Search functionality
    └── File serving
```

## Key Improvements Made

### 1. Clean Implementation
- Removed redundant files and scripts
- Focused on essential components only
- Streamlined codebase structure

### 2. CVS Pharmacy Branding
- Updated all UI text and branding to CVS Pharmacy
- Changed icons from heart to pills
- Updated system prompts for pharmacy focus
- Pre-populated pharmacy-specific questions

### 3. Document Integration
- PDF indexing service for GyaniNuxeo documents
- Search integration in chat responses
- Direct links to source documents
- Categorization by document type

### 4. Enhanced Functionality
- Working login system (any credentials accepted)
- Improved chat responses with document references
- Thumbs up/down feedback system
- Document download capabilities

## File Structure

### Core Application Files
- `app/main.py` - Main FastAPI application
- `app/services/pdf_indexing_service.py` - Document indexing
- `app/api/routes/documents.py` - Document API
- `app/system_prompts/cvs_pharmacy_knowledge_assist_prompt.md` - System prompt

### Frontend Files
- `static/index.html` - Main UI with CVS branding
- `static/js/conversation-manager.js` - Updated with pharmacy questions
- `static/styles.css` - CVS-themed styling

### Documents
- `GyaniNuxeo/` - Folder containing pharmacy documents to be indexed
- `document_index.json` - Auto-generated document index

## Development Notes

### Document Indexing
The PDF indexing service automatically:
1. Scans the GyaniNuxeo folder for supported document types
2. Extracts metadata (filename, size, category, keywords)
3. Creates searchable index entries
4. Provides fast search capabilities
5. Serves documents via API endpoints

### Search Integration
Chat responses automatically include relevant document links when:
1. User queries match document content
2. Keywords align with indexed documents
3. Categories match the query context

### Feedback System
The thumbs up/down system:
1. Tracks feedback per message and user
2. Requires comments for negative feedback
3. Prevents duplicate feedback
4. Stores feedback for analysis

## Future Enhancements

Potential improvements for production deployment:
1. **Full Text Search** - Extract and index document content
2. **Advanced Authentication** - Integration with CVS systems
3. **Enhanced Document Processing** - OCR for scanned documents
4. **Analytics Dashboard** - Usage and feedback analytics
5. **Integration APIs** - Connect to CVS pharmacy systems

## Troubleshooting

### Server Won't Start
1. Check Python installation: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check port availability: `netstat -an | findstr :8080`

### Documents Not Indexing
1. Verify GyaniNuxeo folder exists
2. Check file permissions
3. Review server logs for errors
4. Trigger manual reindex: `GET /api/documents/reindex`

### Login Issues
Currently any credentials work in development mode. For production:
1. Update authentication system
2. Configure proper user management
3. Set up secure session handling

## Support

This is a focused implementation for CVS Pharmacy Knowledge Assist. The system provides essential functionality for pharmacy staff support with clean, maintainable code and comprehensive document integration.
