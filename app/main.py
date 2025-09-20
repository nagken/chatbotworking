"""
CVS Pharmacy Knowledge Assist - Pharmacy Support Assistant
Natural Language → LLM → Pharmacy Knowledge Base → Support Resources → Chat
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from typing import Optional
import os
import json
from contextlib import asynccontextmanager

# Import core services
from .services.llm_service import LLMService
from .services.pdf_indexing_service import get_pdf_indexing_service
from .models.schemas import ChatResponseExtract
from .config import config

# Import API routes
from .api.main import api_router
from .services.service_locator import set_llm_service

# Import database
from .database import init_database, close_database

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

# Global services
llm_service: Optional[LLMService] = None

# Define the lifespan of the app (startup and shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services and database connections"""
    global llm_service

    # ===== STARTUP =====
    try:
        # Initialize database connection
        logger.info("Initializing database connection...")
        try:
            await init_database()
            logger.info("Database connection initialized successfully")
        except Exception as db_error:
            logger.error(f"Database initialization failed: {db_error}")
            logger.warning("Application will continue without database functionality")
        
        # Initialize LLM service (now supports both regular and streaming methods)
        logger.info("Initializing LLM service with streaming support...")
        llm_service = LLMService()
        
        # Set service in the service locator for routes to use
        set_llm_service(llm_service)
        logger.info("LLM service with streaming support registered with service locator")

        # Initialize PDF indexing service
        logger.info("Initializing PDF indexing service...")
        pdf_service = get_pdf_indexing_service()
        logger.info("PDF indexing service initialized successfully")

        # read the system prompt
        with open("app/system_prompts/cvs_pharmacy_knowledge_assist_prompt.md", "r") as f:
            system_prompt = f.read()

        try:
            # update the data agent with the latest system prompt
            llm_service.update_data_agent("cvs-pharmacy-knowledge-assist", system_prompt, "", "")
            logger.info(f"CVS Pharmacy Knowledge Assist agent updated successfully. Current data_agent_id: {llm_service.data_agent_id}")

        except Exception as e:
            # if the data agent doesn't exist, create it
            logger.warning(f"Error updating CVS Pharmacy agent, will create it: {e}")
            llm_service.create_data_agent("cvs-pharmacy-knowledge-assist", system_prompt, "", "")
            logger.info(f"CVS Pharmacy Knowledge Assist agent created successfully. Current data_agent_id: {llm_service.data_agent_id}")

        logger.info("All services initialized successfully - ready to accept requests")

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")

    yield
    
    # ===== SHUTDOWN =====
    logger.info("Shutting down application...")
    
    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
    
    logger.info("Application shutdown complete")   

# Create FastAPI app
app = FastAPI(
    title="CVS Pharmacy Knowledge Assist",
    description="CVS Pharmacy Knowledge Assist - Pharmacy Support Assistant",
    version=config.APP_VERSION,
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/test-login", include_in_schema=False)
async def test_login_page():
    """Test login endpoint"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Login Test - PSS Knowledge Assist</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .test-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 4px; }
        .success { background: #d4edda; border-color: #c3e6cb; color: #155724; }
        .error { background: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        button { padding: 10px 20px; margin: 10px 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PSS Knowledge Assist - Login Debug</h1>
        
        <div class="test-section">
            <h2>Quick Login Test</h2>
            <button class="btn-primary" onclick="testLogin()">Test Admin Login</button>
            <button class="btn-success" onclick="autoLogin()">Auto Login & Redirect</button>
            <div id="loginResult"></div>
        </div>

        <div class="test-section">
            <h2>Server Status</h2>
            <button class="btn-primary" onclick="checkHealth()">Check Health</button>
            <div id="healthResult"></div>
        </div>
    </div>

    <script>
        async function testLogin() {
            const resultDiv = document.getElementById('loginResult');
            resultDiv.innerHTML = '<p>Testing admin login...</p>';
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: 'admin@pss-knowledge-assist.com',
                        password: 'admin123',
                        remember_me: false
                    })
                });
                
                const result = await response.json();
                
                let html = `
                    <h3>Login Test Result:</h3>
                    <p><strong>Status:</strong> ${response.status}</p>
                    <p><strong>Success:</strong> ${result.success ? '✅ YES' : '❌ NO'}</p>
                    <p><strong>Message:</strong> ${result.message}</p>
                `;
                
                if (result.user) {
                    html += `<p><strong>User:</strong> ${result.user.username} (${result.user.email})</p>`;
                }
                
                html += `
                    <details>
                        <summary>Full Response</summary>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    </details>
                `;
                
                resultDiv.innerHTML = html;
                resultDiv.className = 'test-section ' + (result.success ? 'success' : 'error');
                
            } catch (error) {
                resultDiv.innerHTML = `<p class="error">❌ Error: ${error.message}</p>`;
                resultDiv.className = 'test-section error';
            }
        }

        async function autoLogin() {
            await testLogin();
            
            // Wait a bit then redirect
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }

        async function checkHealth() {
            const resultDiv = document.getElementById('healthResult');
            resultDiv.innerHTML = '<p>Checking server health...</p>';
            
            try {
                const response = await fetch('/api/health');
                const result = await response.json();
                
                resultDiv.innerHTML = `
                    <h3>Health Check Result:</h3>
                    <p class="success">✅ Server is running</p>
                    <p><strong>Status:</strong> ${response.status}</p>
                    <pre>${JSON.stringify(result, null, 2)}</pre>
                `;
                resultDiv.className = 'test-section success';
                
            } catch (error) {
                resultDiv.innerHTML = `<p class="error">❌ Health Check Failed: ${error.message}</p>`;
                resultDiv.className = 'test-section error';
            }
        }

        // Auto-run health check
        window.addEventListener('load', () => {
            checkHealth();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/auth-debug", include_in_schema=False)
async def auth_debug_page():
    """Authentication debug page"""
    return FileResponse("auth-debug.html")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/", include_in_schema=False)
async def api_root():
    """API root endpoint"""
    return {"message": "PSS Knowledge Assist API"}


@app.get("/health", include_in_schema=False)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "PSS Knowledge Assist"}


@app.get("/debug-test", include_in_schema=False)
async def debug_test():
    """Simple debug test route"""
    return {"status": "working", "message": "Debug route is functional"}


@app.get("/quick-test", include_in_schema=False)
async def quick_test():
    """Quick test endpoint to verify all systems"""
    return {
        "status": "ok",
        "message": "PSS Knowledge Assist is running",
        "features": {
            "authentication": "✅ Fallback authentication active",
            "conversations": "✅ Mock conversations available", 
            "chat": "✅ Mock chat responses active",
            "feedback": "✅ Mock feedback storage active"
        },
        "test_urls": {
            "main_app": "/",
            "conversations": "/api/conversations",
            "auth_debug": "/api/auth/debug-session"
        }
    }


@app.get("/documents/{filename:path}", include_in_schema=False)
async def serve_document(filename: str):
    """Serve documents from the GyaniNuxeo folder"""
    try:
        # Construct the full path
        documents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "GyaniNuxeo")
        file_path = os.path.join(documents_dir, filename)
        
        # Security check - ensure the file is within the documents directory
        if not os.path.commonpath([documents_dir, file_path]) == documents_dir:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Determine media type based on extension
        file_ext = os.path.splitext(filename)[1].lower()
        media_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        # Return the file
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=os.path.basename(filename)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving document {filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
