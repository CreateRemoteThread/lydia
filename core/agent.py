#!/usr/bin/env python3

import inspect
from typing import Annotated, get_args, get_origin
import requests
import json
import os
import sys
import time
import random
import string
import core.memory
from typing import Dict

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEBUG_REQUESTS=os.getenv("DEBUG_REQUESTS",default=False)
if DEBUG_REQUESTS is not False:
  print("info: DEBUG_REQUESTS set, dumping requests and response json")
  DEBUG_REQUESTS = True

MAX_RETRY = 10

def fn_to_tool_json(fn,tag=None):
    """
    Convert an annotated Python function into an OpenAI Responses API tool schema.
    """
    sig = inspect.signature(fn)

    properties = {}
    required = []

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    SKIP_FIRST = False
    # arglist = sig.parameters.items()
    # if tag is not None:
    #   arglist = arglist[1:]
    for name, param in sig.parameters.items():
      if tag is not None and SKIP_FIRST is False:
        SKIP_FIRST = True
        continue
      annotation = param.annotation
      description = ""
      py_type = str
      # Handle Annotated[T, "description"]
      if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        py_type = args[0]
        if len(args) > 1:
          description = args[1]
      else:
        py_type = annotation

      json_type = type_map.get(py_type, "string")

      properties[name] = {
        "type": json_type,
        "description": description,
      }

      if param.default is inspect.Parameter.empty:
        required.append(name)
  
    fn_name = fn.__name__
    if tag is not None:
      fn_name += "-" + tag

    return {
      "type": "function",
      "name": fn_name,
      "description": inspect.getdoc(fn) or "",
      "parameters": {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
      },
    }

class Agent:
  def __init__(self, sys_prompt="You are a helpful assistant. Use the ask_user tool to ask the user a question.", api_key=os.getenv("OPENAI_API_KEY",default=None), base_url=os.getenv("OPENAI_BASE_URL",default="https://api.openai.com/v1"), model="gpt-4o", timeout=300.0, tools=[], reasoning=None,max_output_tokens=None):
    self.asst_msg_queue = []
    self.api_key = api_key
    if self.api_key is None:
      self.api_key = input("OPENAI_API_KEY > ").strip()
    self.base_url = base_url
    self.model = model
    self.timeout = timeout
    self.req = {}
    if reasoning is not None:
      self.req["reasoning"] = {"effort":reasoning}
    self.req["include"] = []
    self.req["input"] = []
    self.req["instructions"] = sys_prompt
    self.req["metadata"] = None
    self.req["model"] = model
    self.req["stream"] = False
    # -design note-
    # this is to support routing between nodes - there is no
    # easy way to force a consistent choice, so just grep the
    # output.
    if max_output_tokens is not None:
      self.req["max_output_tokens"] = max_output_tokens
    self.tools = tools          # this is generic tools
    # -design note-
    # this has to stay in __init__ for tagged function calls
    # from hatchery to work (least bad option). hatchery will
    # manually add special calls to this, to handle hatchery-only
    # 
    # functionality (e.g. routing)
    # the tradeoff is inflexibility in adjusting tools mid-prompt
    # but this is good friction [tm] - otherwise the llm can add
    # toolbox shell and toolbox term and it's all downhill from there
    if len(self.tools) > 0: 
      self.req["tools"] = []
      for tl in self.tools:
        self.req["tools"].append(fn_to_tool_json(tl))
    elif "tools" in self.req.keys():
      del(self.req["tools"])

  def flush_history(self):
    self.req["input"] = []  

  def append_tagged_tool(self,func,tag,desc):
    self.req["tools"].append(fn_to_tool_json(func,tag))
    self.tools.append(func)
    self.req["instructions"] += " " + desc
 
  @property
  def headers(self) -> Dict[str, str]:
    hdr =  {
      "Authorization": f"Bearer {self.api_key}",
      "Content-Type": "application/json",
      "User-Agent": "lydia/0.0.3"
    }
    x_portkey_provider = os.getenv("X_PORTKEY_PROVIDER",default=None)
    if x_portkey_provider is not None:
      hdr["x-portkey-provider"] = x_portkey_provider
    return hdr

  def req_single(self,user_input=None):
    global MAX_RETRY, DEBUG_REQUESTS
    local_retry = 0
    if user_input is not None:
      self.req["input"].append({"content":user_input,"role":"user"})
    while local_retry < MAX_RETRY:
      try:
        if DEBUG_REQUESTS:
          print(">>>" * 10)
          print(json.dumps(self.req,indent=2))
          print(">>>" * 10)
        response = requests.post(
          f"{self.base_url}/responses",
          headers = self.headers,
          json = self.req,
          timeout = self.timeout,
          verify=False
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
        sys.exit(-1)

  def req_until_complete(self,user_input):
    print("info: entering req_until_complete")
    data = self.req_loop(user_input)
    print(data)

  def req_loop(self,user_input):
    global DEBUG_REQUESTS
    RETN_DATA = None
    RETN_TOOL = False
    if user_input is None:
      print("fatal: req_loop called with no user input, how did we get here?")
      sys.exit(-1)
    if len(self.asst_msg_queue) != 0:
      for a in self.asst_msg_queue:
        print("info: flushing assistant message from queue to input obj...")
        self.req["input"].append(a)
      self.asst_msg_queue = []
    while True:
      if RETN_DATA is not None and RETN_TOOL is False:
        return RETN_DATA
      elif RETN_DATA is not None and RETN_TOOL is True:
        print(RETN_DATA)
      RETN_DATA = None
      RETN_TOOL = False
      resp = self.req_single(user_input)
      core.memory.memory_fade(self.req["input"])
      if DEBUG_REQUESTS:
        print("<<<" * 10)
        print(json.dumps(resp.json(),indent=2))
        print("<<<" * 10)
      outputs = resp.json()["output"]
      for resp_obj in outputs:
        if resp_obj["type"] == "function_call":
          RETN_TOOL = True
          fn_obj = None
          fn_tag = None
          fn_name = resp_obj["name"]
          if "-" in fn_name:
            (fn_name, fn_tag) = fn_name.split("-")
          for i in self.tools:
            if i.__name__ == fn_name:
              fn_obj = i
              break
          if fn_obj is None:
            print("fatal: could not execute call '%s'" % fn_name)
            return "fatal: could not execute call '%s'" % fn_name
          fn_args = json.loads(resp_obj["arguments"])
          if fn_tag is not None:
            print("info: special call, tagged function")
            respval = fn_obj(fn_tag,**fn_args)
          else:
            respval = fn_obj(**fn_args)
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
          self.asst_msg_queue.append({"content":RETN_DATA,"role":"assistant"})
        elif resp_obj["type"] == "reasoning":
          print("Thinking...")
        else:
          print("fatal: don't know how to handle response object type '%s'" % resp_obj["type"])
          sys.exit(-1)

if __name__ == "__main__":
  print("You probably want /r/vibecoding instead")
  # a = Agent(tools=[ask_user])
  # data = a.req_loop("Write a poem about fruit. Ask the user what type of fruit.") 
  # print(data) 
