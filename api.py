#!/usr/bin/env python3
"""FastAPI server entry point for the Data Enricher API.

Usage:
  python api.py
  python api.py --host 0.0.0.0 --port 8000
"""
import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

import uvicorn
from src.server.api import app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Enricher API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    logger.info("Data Enricher API starting on http://%s:%s", args.host, args.port)
    logger.info("Open http://localhost:%s for the web UI", args.port)
    uvicorn.run("src.server.api:app", host=args.host, port=args.port, reload=args.reload)
