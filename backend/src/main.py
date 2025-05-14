from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import firebase_admin
from .api import (
    users,
    documents,
    chat,
    auth,
    chatbots,
    integrations,
    diagnostics,
    settings
)
import argparse
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Chatbot Platform API",
    description="Backend API for the Chatbot Platform",
    version="0.1.0"
)

# Debug middleware
@app.middleware("http")
async def log_request_info(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    logger.info(f"Request headers: {request.headers}")
    
    response = await call_next(request)
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {response.headers}")
    
    return response

# Configure CORS with debug logging
# The origins list includes URLs where the frontend might be hosted
origins = [
    "http://localhost:3000",  # Frontend development server
    "http://localhost:8000",  # Backend server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

logger.info(f"Configuring CORS with allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Chatbot Platform API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with detailed information"""
    try:
        # Check if Firebase is initialized
        firebase_status = "OK" if firebase_admin._apps else "Not initialized"
        
        # Return detailed health information
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "firebase": firebase_status,
                "api": "running"
            },
            "environment": os.environ.get("ENVIRONMENT", "development")
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# Widget JS endpoint
@app.get("/widget/{chatbot_id}.js")
async def get_widget_js(chatbot_id: str):
    try:
        logger.info(f"Serving widget JS for chatbot ID: {chatbot_id}")
        file_path = "static/widget.js"
        
        # Log current working directory and absolute path
        current_dir = os.getcwd()
        abs_path = os.path.abspath(file_path)
        logger.info(f"Current working directory: {current_dir}")
        logger.info(f"Attempting to serve widget from: {abs_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Widget file not found at {file_path}")
            logger.error(f"Absolute path: {abs_path}")
            raise HTTPException(status_code=404, detail="Widget file not found")
            
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            logger.error(f"Widget file is not readable at {file_path}")
            logger.error(f"File permissions: {oct(os.stat(file_path).st_mode)}")
            raise HTTPException(status_code=500, detail="Widget file is not accessible")
            
        # Get absolute path for logging
        abs_path = os.path.abspath(file_path)
        logger.info(f"Serving widget from absolute path: {abs_path}")
        
        # Try to read file content for verification
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                logger.info(f"Successfully read widget file ({len(content)} bytes)")
        except Exception as e:
            logger.error(f"Error reading widget file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error reading widget file: {str(e)}")
        
        return FileResponse(
            file_path,
            media_type="application/javascript",
            headers={
                "Content-Disposition": f"inline; filename=widget-{chatbot_id}.js",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error serving widget for chatbot {chatbot_id}: {str(e)}")
        logger.error(f"Current working directory: {os.getcwd()}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chatbots.router, prefix="/api/chatbots", tags=["chatbots"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["diagnostics"])

# Mount static files directory
try:
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files directory mounted successfully")
except Exception as e:
    logger.error(f"Failed to mount static files directory: {e}")

# Test endpoint that doesn't require authentication
@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint that doesn't require authentication"""
    return {
        "message": "API is working correctly",
        "timestamp": datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser(description="Run the ChatSphere API server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("API_PORT", 8000)),
                      help="Port to run the server on (default: 8000)")
    parser.add_argument("--host", type=str, default=os.environ.get("API_HOST", "0.0.0.0"),
                       help="Host to run the server on (default: 0.0.0.0)")
    args = parser.parse_args()
    
    port = args.port
    host = args.host
    
    logger.info(f"Starting server on {host}:{port}")
    try:
        uvicorn.run("src.main:app", host=host, port=port, reload=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()