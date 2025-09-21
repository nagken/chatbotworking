"""
Documents API routes for CVS Pharmacy Knowledge Assist
Handles document search and serving
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path

from ...services.pdf_indexing_service import get_pdf_indexing_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search")
async def search_documents(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
) -> Dict[str, Any]:
    """
    Search pharmacy documents
    """
    try:
        pdf_service = get_pdf_indexing_service()
        results = pdf_service.search_documents(query, limit)
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "categories": pdf_service.get_categories()
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Error searching documents")

@router.get("/categories")
async def get_document_categories() -> Dict[str, Any]:
    """
    Get all document categories
    """
    try:
        pdf_service = get_pdf_indexing_service()
        return {
            "categories": pdf_service.get_categories(),
            "stats": pdf_service.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Error getting categories")

@router.get("/stats")
async def get_document_stats() -> Dict[str, Any]:
    """
    Get document indexing statistics
    """
    try:
        pdf_service = get_pdf_indexing_service()
        return pdf_service.get_stats()
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting stats")

@router.get("/reindex")
async def reindex_documents() -> Dict[str, Any]:
    """
    Trigger document reindexing
    """
    try:
        pdf_service = get_pdf_indexing_service()
        pdf_service.scan_documents()
        
        return {
            "status": "success",
            "message": "Documents reindexed successfully",
            "stats": pdf_service.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Error reindexing documents: {e}")
        raise HTTPException(status_code=500, detail="Error reindexing documents")

@router.get("/download/{file_path:path}")
async def download_document(file_path: str):
    """
    Download or serve a document file
    """
    try:
        logger.info(f"🔍 Looking for document: '{file_path}'")
        pdf_service = get_pdf_indexing_service()
        
        # Try direct path lookup first
        doc_info = pdf_service.get_document_info(file_path)
        logger.info(f"📄 Direct lookup result: {doc_info is not None}")
        
        # If not found, try filename lookup
        if not doc_info:
            doc_info = pdf_service.find_document_by_filename(file_path)
            logger.info(f"📄 Filename lookup result: {doc_info is not None}")
        
        if not doc_info:
            logger.warning(f"❌ Document not found: '{file_path}'")
            raise HTTPException(status_code=404, detail="Document not found")
        
        full_path = doc_info['full_path']
        logger.info(f"✅ Found document: {doc_info['filename']}")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        # Return file for download/viewing
        return FileResponse(
            path=full_path,
            filename=doc_info['filename'],
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving document {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Error serving document")

@router.get("/view/{file_path:path}")
async def view_document_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a document
    """
    try:
        pdf_service = get_pdf_indexing_service()
        doc_info = pdf_service.get_document_info(file_path)
        
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove internal paths for security
        safe_doc_info = doc_info.copy()
        safe_doc_info.pop('full_path', None)
        
        return {
            "document": safe_doc_info,
            "download_url": f"/api/documents/download/{file_path}",
            "exists": os.path.exists(doc_info['full_path'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Error getting document info")
