# CVS Pharmacy Knowledge Assist - Deployment & Testing Guide

## Overview
This document provides comprehensive instructions for deploying and testing the CVS Pharmacy Knowledge Assist chatbot application.

## Quick Start

### Prerequisites
- Python 3.11+ installed
- Internet connection for package installation
- PDF documents in the `GyaniNuxeo` folder for indexing

### Starting the Server

#### Method 1: Using the Startup Script
```bash
# Run the startup script
start_server.bat
```

#### Method 2: Manual Start
```bash
# Navigate to project directory
cd c:\chatbotsep16

# Install dependencies (first time only)
"C:/Program Files/Python/311/python.exe" -m pip install -r requirements.txt

# Start the server
"C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Accessing the Application
- **Web Interface**: http://localhost:8080
- **Login Credentials**:
  - Email: `admin@cvs-pharmacy-knowledge-assist.com`
  - Password: `admin123`

## Testing Checklist

### 1. Server Health Check
- [ ] Server starts without errors
- [ ] Health endpoint responds: http://localhost:8080/api/health/health
- [ ] Static files load correctly
- [ ] Login page displays with CVS branding

### 2. Authentication Testing
- [ ] Login form accepts test credentials
- [ ] Invalid credentials are rejected
- [ ] Session management works correctly
- [ ] Logout functionality works

### 3. Chat Functionality
- [ ] Chat interface loads properly
- [ ] Pre-populated pharmacy questions appear
- [ ] Messages can be sent and received
- [ ] CVS Pharmacy system prompt is active
- [ ] Responses are relevant to pharmacy context

### 4. Document Search & Indexing
- [ ] PDF documents are indexed from `GyaniNuxeo` folder
- [ ] Document search returns relevant results
- [ ] Document links are clickable and functional
- [ ] Download functionality works for PDFs
- [ ] Search results include source document references

### 5. Feedback System
- [ ] Thumbs up/down buttons appear on responses
- [ ] Feedback can be submitted successfully
- [ ] Feedback is stored properly

### 6. UI/UX Testing
- [ ] CVS red color scheme is applied
- [ ] Responsive design works on different screen sizes
- [ ] All buttons and controls function properly
- [ ] Loading states and error messages display correctly

## API Endpoints Reference

### Core Endpoints
- `GET /` - Main application interface
- `GET /api/health/health` - Application health status
- `POST /api/auth/login` - User authentication
- `POST /api/chat/message` - Send chat message
- `GET /api/documents/search` - Search documents
- `GET /api/documents/download/{filename}` - Download document
- `POST /api/feedback/submit` - Submit feedback

### Testing API Endpoints
You can test API endpoints using tools like curl or Postman:

```bash
# Health check
curl http://localhost:8080/api/health/health

# Document search
curl "http://localhost:8080/api/documents/search?query=medication"

# Login (requires proper headers and authentication)
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cvs-pharmacy-knowledge-assist.com","password":"admin123"}'
```

## Troubleshooting

### Common Issues

#### Server Won't Start
1. **Python not found**: Ensure Python 3.11+ is installed and in PATH
2. **Port already in use**: Check if another application is using port 8080
3. **Missing dependencies**: Run `pip install -r requirements.txt`
4. **Module import errors**: Verify all files are in correct directory structure

#### Authentication Issues
1. **Login fails**: Verify credentials match exactly (case-sensitive)
2. **Session expires**: This is normal for development mode
3. **No login form**: Check if static files are being served correctly

#### Document Search Not Working
1. **No PDFs found**: Ensure `GyaniNuxeo` folder contains PDF files
2. **Search returns empty**: PDFs may not be indexed yet (wait a few seconds after startup)
3. **Download fails**: Check file permissions and paths

#### Chat Not Responding
1. **No LLM service**: Check if external LLM service is configured
2. **Network issues**: Verify internet connection for external services
3. **System prompt issues**: Check if prompt file exists and loads correctly

### Logs and Debugging
- Server logs appear in the terminal/console
- Check browser developer tools for frontend errors
- Use debugging mode by setting `LOG_LEVEL=DEBUG` in environment

## Production Deployment Notes

### Security Considerations
- Change default login credentials
- Implement proper session management
- Add HTTPS/TLS encryption
- Restrict file access permissions
- Validate all user inputs

### Performance Optimization
- Implement proper caching for document search
- Add database connection pooling
- Optimize PDF indexing process
- Add request rate limiting

### Monitoring
- Set up health check monitoring
- Implement logging aggregation
- Monitor document indexing performance
- Track user feedback and usage analytics

## File Structure Summary
```
c:\chatbotsep16\
├── app/                          # Main application code
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration settings
│   ├── api/                      # API routes
│   ├── services/                 # Business logic services
│   ├── database/                 # Database connections and models
│   └── system_prompts/           # AI system prompts
├── static/                       # Frontend files (HTML, CSS, JS)
├── GyaniNuxeo/                   # PDF documents for indexing
├── requirements.txt              # Python dependencies
├── start_server.bat              # Server startup script
└── test_server.py                # Server testing script
```

## Support and Maintenance

### Regular Maintenance Tasks
1. **Update dependencies**: Regularly update `requirements.txt`
2. **Document management**: Add/remove PDFs in `GyaniNuxeo` folder
3. **System prompt updates**: Modify prompts in `system_prompts/` folder
4. **Backup data**: Backup database and document files
5. **Performance monitoring**: Monitor server performance and logs

### Getting Help
- Check application logs for error details
- Review this documentation for common solutions
- Test individual components using the provided test scripts
- Verify all prerequisites are met

---
*CVS Pharmacy Knowledge Assist - Healthcare Support Assistant*
*Last updated: September 16, 2025*
