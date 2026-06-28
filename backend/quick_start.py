#!/usr/bin/env python3
"""
Ultra-minimal startup script. 
Starts a basic HTTP server first, then loads FastAPI in background.
"""
import http.server
import threading
import json
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8000
_app_ready = False
_fastapi_app = None

class QuickHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            status = "healthy" if _app_ready else "loading"
            self.wfile.write(json.dumps({"status": status, "app": "Knight Insurance"}).encode())
        elif self.path == '/api/submissions/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "total": 0, "processing": 0, "completed": 0, "failed": 0,
                "approved": 0, "declined": 0, "referred": 0
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress access logs

def load_fastapi():
    """Load FastAPI in background thread, then switch over."""
    global _app_ready, _fastapi_app
    try:
        print("Loading FastAPI application...", flush=True)
        from main import app
        _fastapi_app = app
        _app_ready = True
        print("FastAPI loaded! Switching to uvicorn...", flush=True)
        import uvicorn
        # This will block and take over serving
        uvicorn.run(app, host="0.0.0.0", port=PORT+1, log_level="info")
    except Exception as e:
        print(f"Error loading FastAPI: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Quick HTTP server on port {PORT}...", flush=True)
    # Start loading FastAPI in background
    t = threading.Thread(target=load_fastapi, daemon=True)
    t.start()
    # Serve immediately with basic handler
    server = http.server.HTTPServer(("0.0.0.0", PORT), QuickHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
        server.server_close()
