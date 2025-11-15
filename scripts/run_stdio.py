#!/usr/bin/env python3
"""
Run MCP server in STDIO mode for Claude Desktop
Uses your local Azure credentials (az login)
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the server
from src.server import mcp

if __name__ == "__main__":
    # Run with stdio transport (default for MCP)
    mcp.run()
