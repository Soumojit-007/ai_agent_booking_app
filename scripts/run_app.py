#!/usr/bin/env python3
"""
Application Runner Script
Starts both FastAPI backend and Streamlit frontend.
"""

import subprocess
import sys
import time
import os

def run_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

def run_frontend():
    """Start the Streamlit frontend"""
    print("🌐 Starting Streamlit frontend...")
    return subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/streamlit_app.py", 
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

def main():
    """Main application runner"""
    print("📅 AI Calendar Booking Agent")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Please create one using .env.example as template")
        return
    
    # Check if Google credentials exist
    if not os.path.exists('credentials/google_credentials.json'):
        print("⚠️  Google credentials not found. Please run setup_google_auth.py first")
        return
    
    processes = []
    
    try:
        # Start backend
        backend_process = run_backend()
        processes.append(backend_process)
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        # Start frontend
        frontend_process = run_frontend()
        processes.append(frontend_process)
        
        print("\n✅ Both services started successfully!")
        print("🔗 API: http://localhost:8000")
        print("🔗 Frontend: http://localhost:8501")
        print("\n Press Ctrl+C to stop all services")
        
        # Wait for processes
        for process in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        # Terminate all processes
        for process in processes:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
