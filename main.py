#!/usr/bin/env python3
"""
VeriGreen - Satellite Forest Monitoring System
Main entry point for the application
"""
import uvicorn
import sys
import os
from pathlib import Path

# Add the backend/src directory to Python path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

try:
    from app import app
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Make sure you have installed the required dependencies:")
    print("cd backend && pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Run the VeriGreen API server"""
    print("🌲 VeriGreen - Satellite Forest Monitoring System")
    print("=" * 50)
    print("Starting API server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main() 