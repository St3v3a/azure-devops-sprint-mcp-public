#!/usr/bin/env python3
"""
Docker STDIO Bridge for Claude Desktop (Windows)

This script connects Claude Desktop (Windows) to the Azure DevOps MCP server
running in Docker (WSL) using stdio transport.

Usage:
    python run_docker_stdio.py

Configuration in Claude Desktop (Windows):
    {
      "mcpServers": {
        "azure-devops": {
          "command": "python",
          "args": ["C:\\path\\to\\run_docker_stdio.py"]
        }
      }
    }

Requirements:
    - Docker Desktop running (which includes WSL integration)
    - Container 'azure-devops-mcp' must be running
    - Python 3.8+ on Windows
"""
import subprocess
import sys
import os

# Container name (must match docker-compose.yml)
CONTAINER_NAME = "azure-devops-mcp"

def main():
    """
    Forward stdin/stdout between Claude Desktop and Docker container
    """
    # Log startup to stderr (Claude Desktop ignores stderr)
    sys.stderr.write("=== Azure DevOps MCP Docker STDIO Bridge ===\n")
    sys.stderr.write(f"Connecting to Docker container: {CONTAINER_NAME}\n")
    sys.stderr.flush()

    try:
        # Run the MCP server in stdio mode inside the Docker container
        # -i: Keep stdin open
        # -e: Set environment variable for stdio transport
        process = subprocess.Popen(
            [
                "docker", "exec", "-i",
                "-e", "MCP_TRANSPORT=stdio",
                CONTAINER_NAME,
                "python", "-m", "src.server"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0  # Unbuffered
        )

        sys.stderr.write("Connected to Docker container successfully\n")
        sys.stderr.write("Server ready for JSON-RPC messages\n")
        sys.stderr.flush()

        # Forward stdin to container
        def forward_stdin():
            try:
                while True:
                    line = sys.stdin.buffer.readline()
                    if not line:
                        break
                    process.stdin.write(line)
                    process.stdin.flush()
            except Exception as e:
                sys.stderr.write(f"stdin error: {e}\n")
                sys.stderr.flush()
            finally:
                process.stdin.close()

        # Forward stdout from container
        def forward_stdout():
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    sys.stdout.buffer.write(line)
                    sys.stdout.buffer.flush()
            except Exception as e:
                sys.stderr.write(f"stdout error: {e}\n")
                sys.stderr.flush()

        # Forward stderr from container (for debugging)
        def forward_stderr():
            try:
                while True:
                    line = process.stderr.readline()
                    if not line:
                        break
                    sys.stderr.write(line.decode('utf-8', errors='replace'))
                    sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"stderr forward error: {e}\n")
                sys.stderr.flush()

        # Start forwarding threads
        import threading
        stdin_thread = threading.Thread(target=forward_stdin, daemon=True)
        stdout_thread = threading.Thread(target=forward_stdout, daemon=True)
        stderr_thread = threading.Thread(target=forward_stderr, daemon=True)

        stdin_thread.start()
        stdout_thread.start()
        stderr_thread.start()

        # Wait for process to complete
        process.wait()

        sys.stderr.write("Docker container process exited\n")
        sys.stderr.flush()

    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Docker exec failed: {e}\n")
        sys.stderr.write(f"Make sure Docker Desktop is running\n")
        sys.stderr.write(f"Make sure container '{CONTAINER_NAME}' is running: docker ps\n")
        sys.stderr.flush()
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write("Docker command not found\n")
        sys.stderr.write("Make sure Docker Desktop is installed and in PATH\n")
        sys.stderr.flush()
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    main()
