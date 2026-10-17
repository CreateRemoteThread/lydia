#!/usr/bin/env python3

from pathlib import Path
import os
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MCPLoader = None
API_PATH = "/"

def setMcpLoader(mcp_loader):
  global MCPLoader
  MCPLoader = mcp_loader

def getDataPath(template_name):
  file_path = os.path.join(os.path.dirname(__file__), "../moonsugar", template_name)
  return file_path

class MCPHandler(BaseHTTPRequestHandler):
  def _send_json(self, obj, status=200):
    data = json.dumps(obj).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(data)))
    self.end_headers()
    self.wfile.write(data)

  def do_POST(self):
    global MCPLoader
    if self.path != API_PATH:
      fn = getDataPath(self.path.lstrip("/"))
      if not os.path.isfile(fn):
        fn = getDataPath("error")
      with open(fn,"rb") as f:
        data = f.read()
      self.send_response(200)
      self.send_header("Content-Type", "text/html")
      self.send_header("Content-Length", str(len(data)))
      self.end_headers()
      self.wfile.write(data)
      return
    length = int(self.headers.get("Content-Length", "0"))
    body = self.rfile.read(length) if length else b"{}"
    try:
      req = json.loads(body.decode("utf-8"))
    except Exception:
      self._send_json({
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32700, "message": "Parse error"},
      }, status=400)
      return

    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
      self._send_json({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
          "protocolVersion": "2024-11-05",
          "serverInfo": {"name": "skooma-cat", "version": "0.1.0"},
          "capabilities": {
            "tools": {}
          }
        }
      })
      return

    if method == "tools/list":
      self._send_json({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
          "tools": MCPLoader.get_json()
        }
      })
      return

    if method == "tools/call":
      name = params.get("name")
      args = params.get("arguments")
      result = MCPLoader.mcp_call(name,args)
      if result is not None:
        self._send_json({
          "jsonrpc": "2.0",
          "id": req_id,
          "result": {
            "content": [
              {
                "type": "text",
                "text": result
              }
            ],
            "isError": False
          }
        })
      else:
        self._send_json({
          "jsonrpc": "2.0",
          "id": req_id,
          "error": {"code": -32601, "message": "Unknown tool"}
        }, status=404)
      return

    if method == "notifications/initialized":
      self.send_response(204)
      self.end_headers()
      return

    self._send_json({
      "jsonrpc": "2.0",
      "id": req_id,
      "error": {"code": -32601, "message": "Method not found"}
    }, status=404)

  def do_GET(self):
    if self.path == "/favicon.ico":
      self.send_response(404)
      self.end_headers()
      return
    elif self.path != API_PATH:
      fn = getDataPath(self.path.lstrip("/"))
      if not os.path.isfile(fn):
        fn = getDataPath("error")
      with open(fn,"rb") as f:
        data = f.read()
      self.send_response(200)
      self.send_header("Content-Type", "text/html")
      self.send_header("Content-Length", str(len(data)))
      self.end_headers()
      self.wfile.write(data)
      return
    self._send_json({
      "name": "skooma-cat",
      "status": "ok",
      "endpoint": "/"
    })

if __name__ == "__main__":
  host = "127.0.0.1"
  port = 8000
  httpd = ThreadingHTTPServer((host, port), MCPHandler)
  print(f"Serving MCP HTTP server on http://{host}:{port}")
  httpd.serve_forever()
