#!/usr/bin/env python3

import inspect
import core.config
from typing import Annotated, get_args, get_origin
import requests
import json
import os
import sys
import time
import random
import string
import copy
import core.memory
import core.mcp
from typing import Dict

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEBUG_REQUESTS = None
SSL_VERIFY = core.config.getenv("SSL_VERIFY","True") == "True"
MAX_RETRY = 10

def anthropic_json_fix(fn_array):
  out = []
  for f in fn_array:
    f["type"] = "custom"
    if "input_schema" not in f.keys():
      f["input_schema"] = f["parameters"]
      f.pop("parameters")
    if "annotations" in f.keys():
      f.pop("annotations")
    if "execution" in f.keys():
      f.pop("execution")
    out.append(f)
  return out

class BaseAgent:
  def __init__(self,sys_prompt,api_key,base_url,model,timeout,reasoning,max_output_tokens):
    self.asst_msg_queue = []
    self.api_key = api_key
    if self.api_key is None:
      self.api_key = input("OPENAI_API_KEY > ").strip()
    self.model = model
    self.mcploader = None
    self.timeout = timeout
    self.req = {}
    if reasoning is not None:
      self.req["reasoning"] = {"effort":reasoning}
    self.req["metadata"] = None
    self.req["model"] = model
    # self.req["prompt_cache_key"] = "lydia-v1"
    self.req["stream"] = False
    if max_output_tokens is not None:
      self.req["max_output_tokens"] = max_output_tokens

  def __deepcopy__(self, memo):
    result = self.__class__.__new__(self.__class__)
    memo[id(self)] = result
    for key, value in self.__dict__.items():
      if key == "mcploader":
        setattr(result, key, core.mcp.MCPLoader())
      else:
        setattr(result, key, copy.deepcopy(value, memo))
    return result
  
  def duplicate(self):
    return copy.deepcopy(self)

  def flush_history(self):
    self.asst_msg_queue = []
    self.req[self.sz_memory] = []  

  def set_mcploader(self,mcploader):
    self.mcploader = mcploader
    self.mcploader.execute_pytool_hooks(self)

  def crashlanding(self):
    prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    fn = "log-%s.crash" % prefix
    with open(fn,"w") as f:
      f.write(json.dumps(self.req[self.sz_memory],indent=2))
    print("crash: dumping memory to %s" % fn)

  def req_single(self,user_input=None):
    global MAX_RETRY, DEBUG_REQUESTS
    self.build_request(user_input)
    local_retry = 0
    while local_retry < MAX_RETRY:
      try:
        if DEBUG_REQUESTS:
          print(">>>" * 10)
          print(json.dumps(self.req,indent=2))
          print(">>>" * 10)
        global SSL_VERIFY
        response = requests.post(
          self.base_url,
          headers = self.headers,
          json = self.req,
          timeout = self.timeout,
          verify=SSL_VERIFY
        )
        return response
      except requests.exceptions.ReadTimeout:
        print("warn: timeout (%d/%d)" % (local_retry,MAX_RETRY))
        local_retry += 1
        sleeptime = random.randint(1,5)
        time.sleep(sleeptime)
        continue
      except Exception as e:
        print("fatal: what the absolute fuck")
        print(e)
        self.crashlanding()
        sys.exit(-1)

  def req_until_complete(self,user_input):
    print("info: entering req_until_complete")
    data = self.req_loop(user_input)
    print(data)

class ResponseAgent(BaseAgent):
  def __init__(self, sys_prompt="You are a helpful assistant.", api_key=core.config.getenv("OPENAI_API_KEY",default=None), base_url=core.config.getenv("OPENAI_BASE_URL",default="https://api.openai.com/v1"), model="gpt-4o", timeout=300.0, reasoning=None,max_output_tokens=None):
    super().__init__(sys_prompt,api_key,base_url,model,timeout,reasoning,max_output_tokens)
    print("core: Hello from ResponseAgent")
    self.sz_memory = "input"
    self.req["instructions"] = sys_prompt
    self.base_url = base_url.rstrip("/") + "/responses"
    self.req["prompt_cache_key"] = "lydia-v1"
    self.req["input"] = []
 
  def build_request(self,user_input):
    self.req["tools"] = []
    if self.mcploader is not None:
      self.req["tools"] += self.mcploader.get_json()
    if len(self.req["tools"]) == 0:
      del(self.req["tools"])
    if user_input is not None:
      self.req["input"].append({"content":[{"type":"input_text","text":user_input}],"role":"user"})

  @property
  def headers(self) -> Dict[str, str]:
    hdr =  {
      "Content-Type": "application/json",
      "User-Agent": "lydia/0.0.3"
    }
    hdr["Authorization"] = f"Bearer {self.api_key}"
    x_portkey_provider = core.config.getenv("X_PORTKEY_PROVIDER",default=None)
    if x_portkey_provider is not None:
      hdr["x-portkey-provider"] = x_portkey_provider
    return hdr

  def req_loop(self,user_input,max_think=-1):
    global DEBUG_REQUESTS
    if DEBUG_REQUESTS is None:
      DEBUG_REQUESTS = core.config.getenv("DEBUG_REQUESTS",default=False)
      if DEBUG_REQUESTS is not False:
        print("info: DEBUG_REQUESTS set, dumping requests and response json")
        DEBUG_REQUESTS = True
    RETN_DATA = None
    RETN_TOOL = False
    if user_input is None:
      print("fatal: req_loop called with no user input, how did we get here?")
      sys.exit(-1)
    send_user_input_once = True
    if len(self.asst_msg_queue) != 0:
      for a in self.asst_msg_queue:
        print("info: flushing assistant message from queue to input obj...")
        self.req["input"].append(a)
      self.asst_msg_queue = []
    core.memory.memory_fade(self.req["input"])
    while True:
      if RETN_DATA is not None and RETN_TOOL is False:
        return RETN_DATA
      elif RETN_DATA is not None and RETN_TOOL is True:
        print(RETN_DATA)
      RETN_DATA = None
      RETN_TOOL = False
      if send_user_input_once:
        resp = self.req_single(user_input)
        send_user_input_once = False
      else:
        resp = self.req_single(None)
      core.memory.memory_fade_gradual(self.req["input"])
      # print(len(self.req["input"]))
      if DEBUG_REQUESTS:
        print("<<<" * 10)
        print(json.dumps(resp.json(),indent=2))
        print("<<<" * 10)
      try:
        if "output" not in resp.json().keys():
          print("fatal: response did not contain 'output'")
          print(json.dumps(resp.json(),indent=2))
          sys.exit(-1)
      except:
        print("fatal: what the absolute fuck part 2")
        print(resp)
        self.crashlanding()
        sys.exit(-1)
      outputs = resp.json()["output"]
      for resp_obj in outputs:
        if resp_obj["type"] == "function_call":
          RETN_TOOL = True
          fn_obj = None
          fn_name = resp_obj["name"]
          try:
            fn_args = json.loads(resp_obj["arguments"])
          except:
            print("agent: error laoding argument")
            print(resp_obj)
            sys.exit(0)
          if fn_obj is None: # did not find the function
            if self.mcploader is None:
              print("fatal: could not execute call '%s'" % fn_name)
              return "fatal: could not execute call '%s'" % fn_name
            else:
              print("info: attempting to pass to mcp loader")
              mcp_ret = self.mcploader.mcp_call(fn_name,fn_args)
              if mcp_ret is None:
                print("warn: mcp function '%s' forgot to return, overriding with 'ok'" % fn_name)
                respval = "ok"
              else:
                respval = str(mcp_ret)
          else: # found the function first pass
            print("info: calling regular function '%s'" % fn_name)
            respval = fn_obj(**fn_args)
            # -design note-: too unwieldy, don't use this.
            # if fn_name == "create_worker":
            #   print("info: wiping memory of prompt argument")
            #   fn_args["prompt"] = ""
            #  resp_obj["arguments"] = json.dumps(fn_args)
          if "id" in resp_obj.keys():
            CALL_ID = resp_obj["id"]
          else:
            CALL_ID = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
          self.req["input"].append({
            "arguments":resp_obj["arguments"],
            "call_id":CALL_ID,
            "name":resp_obj["name"],
            "type":"function_call",
            "status":"completed"
          })
          self.req["input"].append({
            "call_id":CALL_ID,
            "output":respval,
            "type":"function_call_output",
          })
        elif resp_obj["type"] == "message":
          RETN_DATA = resp_obj["content"][0]["text"]
          self.asst_msg_queue.append({"content":[{"type":"output_text","text":RETN_DATA}],"role":"assistant","type":"message"})
        elif resp_obj["type"] == "reasoning":
          print("Thinking...")
        else:
          print("fatal: don't know how to handle response object type '%s'" % resp_obj["type"])
          sys.exit(-1)

class MessagingAgent(BaseAgent):
  def __init__(self, sys_prompt="You are a helpful assistant.", api_key=core.config.getenv("OPENAI_API_KEY",default=None), base_url=core.config.getenv("OPENAI_BASE_URL",default="https://api.anthropic.com/v1"), model="claude-sonnet-4-6", timeout=300.0, reasoning=None,max_output_tokens=None):
    super().__init__(sys_prompt,api_key,base_url,model,timeout,reasoning,max_output_tokens)
    print("core: Hello from MessagingAgent")
    self.sz_memory = "messages"
    self.req["system"] = [{"type":"text","text":sys_prompt}]
    self.base_url = base_url.rstrip("/") + "/messages"
    self.req["cache_control"] = {"type": "ephemeral"}
    self.req["messages"] = []   
    self.req["max_tokens"] = core.config.getenv("ANTHROPIC_MAX_TOKENS",default=64000)
 
  @property
  def headers(self) -> Dict[str, str]: 
    hdr =  {
      "Content-Type": "application/json",
      "User-Agent": "lydia/0.0.3"
    }
    # "Authorization": f"Bearer {self.api_key}",
    hdr["x-api-key"] = self.api_key  
    hdr["anthropic-version"] = "2023-06-01"
    x_portkey_provider = core.config.getenv("X_PORTKEY_PROVIDER",default=None)
    if x_portkey_provider is not None:
      hdr["x-portkey-provider"] = x_portkey_provider
    return hdr 

  def build_request(self,user_input):
    self.req["tools"] = []
    if self.mcploader is not None:
      self.req["tools"] += anthropic_json_fix(self.mcploader.get_json())
    if len(self.req["tools"]) == 0:
      del(self.req["tools"])
    if user_input is not None:
      sz_type = "text"
      self.req["messages"].append({"content":[{"type":sz_type,"text":user_input}],"role":"user"})

  def req_loop(self,user_input,max_think=-1):
    global DEBUG_REQUESTS
    if DEBUG_REQUESTS is None:
      DEBUG_REQUESTS = core.config.getenv("DEBUG_REQUESTS",default=False)
      if DEBUG_REQUESTS is not False:
        print("info: DEBUG_REQUESTS set, dumping requests and response json")
        DEBUG_REQUESTS = True
    RETN_DATA = None
    RETN_TOOL = False
    if user_input is None:
      print("fatal: req_loop called with no user input, how did we get here?")
      sys.exit(-1)
    send_user_input_once = True
    if len(self.asst_msg_queue) != 0:
      for a in self.asst_msg_queue:
        print("info: flushing assistant message from queue to input obj...")
        self.req["messages"].append(a)
      self.asst_msg_queue = []
    core.memory.memory_fade(self.req["messages"]) 
    while True:
      if RETN_DATA is not None and RETN_TOOL is False:
        return RETN_DATA
      elif RETN_DATA is not None and RETN_TOOL is True:
        print(RETN_DATA)
      RETN_DATA = None
      RETN_TOOL = False
      if send_user_input_once:
        resp = self.req_single(user_input)
        send_user_input_once = False
      else:
        resp = self.req_single(None)
      core.memory.memory_fade_gradual(self.req["messages"])
      # print(len(self.req["messages"]))
      if DEBUG_REQUESTS:
        print("<<<" * 10)
        print(json.dumps(resp.json(),indent=2))
        print("<<<" * 10)
      try:
        if "content" not in resp.json().keys():
          print("fatal: response did not contain 'content'")
          print(json.dumps(resp.json(),indent=2))
          sys.exit(-1)
      except:
        print("fatal: what the absolute fuck part 2")
        print(resp)
        self.crashlanding()
        sys.exit(-1)
      if "stop_reason" in resp.json().keys():
        stopreason = resp.json()["stop_reason"]
        if stopreason == "refusal" and resp.json()["stop_details"]["category"] != None:
          print("stop: refusal (stop_reason:%s)" % resp.json()["stop_details"]["category"])
          sys.exit(-1)
      outputs = resp.json()["content"]
      for resp_obj in outputs:
        if resp_obj["type"] == "tool_use":
          RETN_TOOL = True
          fn_obj = None
          fn_name = resp_obj["name"]
          fn_args = resp_obj["input"]
          if fn_obj is None: # did not find the function
            if self.mcploader is None:
              print("fatal: could not execute call '%s'" % fn_name)
              return "fatal: could not execute call '%s'" % fn_name
            else:
              print("info: attempting to pass to mcp loader")
              mcp_ret = self.mcploader.mcp_call(fn_name,fn_args)
              if mcp_ret is None:
                print("fatal: could not execute (or find in mcp) function '%s'" % fn_name)
                return "fatal: could not execute (or find in mcp) function '%s'" % fn_name
              else:
                respval = str(mcp_ret)
          else: # found the function first pass
            print("info: calling regular function '%s'" % fn_name)
            respval = fn_obj(**fn_args)
          if "id" in resp_obj.keys():
            CALL_ID = resp_obj["id"]
          else:
            CALL_ID = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
          self.req["messages"].append({
            "content":[{
            "input":resp_obj["input"],
            "id":CALL_ID,
            "name":resp_obj["name"],
            "type":"tool_use",
            }],
            "role":"assistant"
          })
          self.req["messages"].append({
            "role":"user",
            "content":[{
            "tool_use_id":CALL_ID,
            "content":respval,
            "type":"tool_result",
            }]
          })
        elif resp_obj["type"] == "text":
          RETN_DATA = resp_obj["text"]
          self.asst_msg_queue.append({"role":"assistant","content":RETN_DATA})
        elif resp_obj["type"] == "reasoning" or resp_obj["type"] == "thinking":
          print("Thinking...")
        else:
          print("fatal: don't know how to handle response object type '%s'" % resp_obj["type"])
          sys.exit(-1)

if __name__ == "__main__":
  print("You probably want /r/vibecoding instead")
