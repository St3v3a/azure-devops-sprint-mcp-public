#!/bin/bash
# Test the MCP bridge with multiple requests

echo "Testing MCP Bridge..."
echo ""

# Create a test script that sends multiple requests
cat << 'EOF' | python mcp_bridge.py
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"resources/list","params":{}}
EOF

echo ""
echo "✅ Bridge test complete!"
