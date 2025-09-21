# CVS Pharmacy Knowledge Assist - System Architecture

## 🏗️ High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CVS Pharmacy Knowledge Assist                │
│                      System Architecture                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│                 │ ◄──────────────────► │                 │
│   Frontend UI   │                      │  FastAPI Server │
│   (HTML/CSS/JS) │                      │    (Python)     │
│                 │                      │                 │
└─────────────────┘                      └─────────────────┘
         │                                        │
         │                                        │
         ▼                                        ▼
┌─────────────────┐                      ┌─────────────────┐
│                 │                      │                 │
│ Browser Storage │                      │   PostgreSQL    │
│ (Conversations) │                      │   Database      │
│                 │                      │                 │
└─────────────────┘                      └─────────────────┘
                                                  │
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │                 │
                                         │ Google Cloud    │
                                         │ Vertex AI       │
                                         │                 │
                                         └─────────────────┘
                                                  │
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │                 │
                                         │ Document Index  │
                                         │ (1,880 PDFs)    │
                                         │                 │
                                         └─────────────────┘
```

## 🔧 Component Details

### 1. **Frontend Layer** (`static/`)
```
static/
├── index.html          # Main application interface
├── styles.css          # Complete styling including new clear chat button
└── js/
    └── conversation-manager.js  # Chat management & new clear functionality
```

**Key Features:**
- **Chat Interface**: Message display with streaming responses
- **Sidebar Navigation**: Conversation list with New Chat and Clear All buttons
- **Document Links**: Clickable buttons for PDF downloads with fuzzy matching
- **Real-time Updates**: Auto-refresh conversation list

### 2. **Backend API Layer** (`app/`)
```
app/
├── main.py                    # FastAPI application entry point
├── api/routes/
│   ├── conversations.py       # CRUD operations + new clear-all endpoint
│   ├── chat.py               # Streaming chat with AI integration
│   ├── documents.py          # PDF serving and search
│   └── auth.py               # User authentication
├── services/
│   ├── llm_service.py        # Google Vertex AI integration
│   ├── pdf_indexing_service.py  # Document search and indexing
│   └── conversation_service.py  # Conversation management
└── database/
    └── models.py             # Database schema definitions
```

**Key APIs:**
- `GET /api/conversations` - List user conversations
- `POST /api/conversations` - Create new conversation
- `DELETE /api/conversations/clear-all` - 🆕 Clear all conversations
- `POST /api/chat/stream` - Streaming AI responses
- `GET /documents/{filename}` - Document downloads

### 3. **Data Storage Layer**

#### **PostgreSQL Database**
```sql
Users Table:
├── id (Primary Key)
├── email
├── created_at
└── updated_at

Conversations Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── title
├── created_at
└── updated_at

Messages Table:
├── id (Primary Key)
├── conversation_id (Foreign Key)
├── content
├── message_type (user/assistant)
└── created_at
```

#### **Document Storage**
```
GyaniNuxeo/                    # Document repository
├── 1,880 PDF files           # CVS policies, procedures, guides
└── document_index.json       # Searchable index for fast lookup
```

### 4. **AI Integration Layer**

#### **Google Cloud Vertex AI**
- **Model**: Gemini Pro with streaming support
- **Data Agent**: `cvs-pharmacy-knowledge-assist`
- **Capabilities**: 
  - Document-aware responses
  - Context understanding
  - Streaming text generation

## 🔄 Data Flow Diagrams

### **New Chat Flow**
```
User Clicks "New Chat"
         │
         ▼
Frontend clears current chat
         │
         ▼
Reset conversation state
         │
         ▼
Show welcome message
         │
         ▼
Focus on input field
```

### **Clear All Chats Flow** 🆕
```
User Clicks "Clear All Chats"
         │
         ▼
Show confirmation dialog
         │
         ▼ (if confirmed)
Frontend sends DELETE /api/conversations/clear-all
         │
         ▼
Backend deletes all user conversations
         │
         ▼
Clear mock store data
         │
         ▼
Return success response
         │
         ▼
Frontend clears local state
         │
         ▼
Reset to welcome screen
```

### **Chat Message Flow**
```
User types message
         │
         ▼
Frontend sends to /api/chat/stream
         │
         ▼
Backend authenticates user
         │
         ▼
Create/update conversation
         │
         ▼
Send to Vertex AI with document context
         │
         ▼
Stream AI response back to frontend
         │
         ▼
Display with document links
         │
         ▼
Save message to database
```

### **Document Download Flow**
```
User clicks document link
         │
         ▼
Frontend requests /documents/{filename}
         │
         ▼
Backend fuzzy matches filename
         │
         ▼
Locate file in GyaniNuxeo/
         │
         ▼
Security check (path validation)
         │
         ▼
Stream file to browser
         │
         ▼
Browser downloads/opens document
```

## 🛡️ Security & Authentication

### **Authentication Flow**
```
User Access
     │
     ▼
Session-based auth (development)
     │
     ▼
Mock user creation if needed
     │
     ▼
Request authorization via middleware
     │
     ▼
API access granted
```

### **Security Measures**
- **Path Validation**: Prevents directory traversal attacks
- **File Type Validation**: Only serves approved document types
- **User Isolation**: Each user sees only their conversations
- **Input Sanitization**: All user inputs are validated

## 🔧 Technology Stack

### **Frontend**
- **HTML5** - Structure and layout
- **CSS3** - Modern styling with flexbox
- **Vanilla JavaScript** - Real-time interaction without frameworks
- **Fetch API** - HTTP communication with backend

### **Backend**
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server with auto-reload
- **SQLAlchemy** - Database ORM with async support
- **Pydantic** - Data validation and serialization

### **Database**
- **PostgreSQL** - Primary data storage
- **Alembic** - Database migrations
- **Connection Pooling** - Efficient database connections

### **AI & Cloud**
- **Google Cloud Vertex AI** - Gemini Pro model
- **Google Auth** - Service authentication
- **Streaming Responses** - Real-time AI interaction

### **Development & Deployment**
- **Git** - Version control (main/feature1 branches)
- **Docker** - Containerization support
- **Auto-reload** - Development efficiency

## 🚀 Current Features

### ✅ **Implemented**
1. **Document Search & Download** - Fuzzy matching, secure serving
2. **Streaming Chat** - Real-time AI responses with context
3. **Conversation Management** - Create, list, switch between chats
4. **Clear All Conversations** - 🆕 Bulk conversation deletion
5. **Document Links** - Clickable references in AI responses
6. **User Authentication** - Session-based with fallback
7. **Database Integration** - PostgreSQL with mock fallback
8. **PDF Indexing** - 1,880 searchable documents

### 🎯 **Architecture Benefits**
- **Scalable**: Modular design allows easy feature additions
- **Resilient**: Database fallback ensures continuity
- **Responsive**: Streaming provides immediate feedback
- **Secure**: Multiple layers of validation and authorization
- **Maintainable**: Clear separation of concerns
- **Fast**: Efficient document indexing and caching

## 📁 Quick File Reference

### **Key Configuration Files**
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Container orchestration
- `alembic.ini` - Database migration config

### **Important Scripts**
- `start_server.bat` - Quick server startup
- `quick_test.py` - Functionality verification
- `test_document_links.py` - Document download testing

This architecture provides a robust, scalable foundation for the CVS Pharmacy Knowledge Assist system with clear separation of concerns and modern development practices.