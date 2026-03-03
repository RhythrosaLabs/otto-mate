#!/usr/bin/env python3
"""Otto Universal AI Server Launcher"""
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, log_level="info")
