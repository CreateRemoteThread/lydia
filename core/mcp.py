#!/usr/bin/env python3

import json
import subprocess
import itertools
import sys
import copy

class MCPHandlerStdio:
  def send_notification(self,method,params=None):
    payload = {
      "jsonrpc":"2.0",
      "method":method,
      "params":params or {}
    }
    self.proc.stdin.write(json.dumps(payload) + "\n")
    self.proc.stdin.flush()


  def send_request(self,method,params=None):
    request_id = next(self._id_counter)
    payload = {
      "jsonrpc":"2.0",
      "id":request_id,
      "method":method,
      "params":params or {}
    }
    self.proc.stdin.write(json.dumps(payload)+ "\n")
    self.proc.stdin.flush()
    line = self.proc.stdout.readline()
    if not line:
      print("fatal: mcp server unexpectedly died")
      print(self.proc.stderr.read())
      sys.exit(-1)
    else:
      return json.loads(line).get("result")

  def fn_call(self,name,params):
    # print("mcp: fn_call hit inside mcp handler")
    r = self.send_request("tools/call",{"name":name,"arguments":params})
    cont = r.get("content")
    if len(cont) == 1 and cont[0]["type"] == "text":
      return cont[0]["text"]
    else:
      return cont

  def __init__(self,command):
    self._id_counter = itertools.count(1)
    self.tool_names = []
    self.proc = subprocess.Popen(command.split(),
      stdin = subprocess.PIPE,
      stdout =subprocess.PIPE,
      stderr = subprocess.PIPE,
      text = True,
      bufsize=1,
    )
    r = self.send_request("initialize",
      {
        "protocolVersion":"2024-11-05",
        "capabilities":{},
        "clientInfo":{
          "name":"lydia",
          "version":"-1"
        }
      }
    )
    # removed: vibe-mcp shits itself with this
    # self.send_notification("notification/initialized")
    r = self.send_request("tools/list")
    self.tools_json = r.get("tools",[])
    for i in self.tools_json:
      self.tool_names.append(i.get("name"))
      i["parameters"] = i.pop("inputSchema") # do this once, here, at loading.

class MCPLoader:
  def __init__(self):
    self.mcplist = []

  def load_mcp(self,mcpname):
    print("mcp: loading '%s'" % mcpname)
    self.mcplist.append(MCPHandlerStdio(mcpname))

  def get_json(self):
    t = []
    for mcp in self.mcplist:
      t += mcp.tools_json 
    for tool in t:
      tool["type"] = "function"
    return t

  def mcp_call(self,fn_name,fn_args):
    print("mcp: mcp_call('%s','%s')" % (fn_name,fn_args))
    for mcp in self.mcplist:
      if fn_name in mcp.tool_names:
        print("mcp: found server hosting '%s'" % fn_name)
        return mcp.fn_call(fn_name,fn_args)
        break
    print("mcp: could not find '%s'" % fn_name)
    return None
    # sys.exit(0)

if __name__ == "__main__":
  print("start")
  m = MCPLoader()
  m.load_mcp("npx -y chrome-devtools-mcp@latest")
  print(json.dumps(m.get_json(),indent=2))
