#!/usr/bin/env python3

import inspect
from typing import Annotated, get_args, get_origin
import requests
import json
import os
import time
import random
from typing import Dict

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEBUG_REQUESTS=os.getenv("DEBUG_REQUESTS",default=False)
if DEBUG_REQUESTS is not False:
  print("info: DEBUG_REQUESTS set, dumping requests and response json")
  DEBUG_REQUESTS = True

MAX_RETRY = 10

def fn_to_tool_json(fn):
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

    for name, param in sig.parameters.items():
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

    return {
        "type": "function",
        "name": fn.__name__,
        "description": inspect.getdoc(fn) or "",
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }

def ask_user(question: Annotated[str, "The question to ask"]):
  return input(question + " > ").strip()

class Agent:
  def __init__(self, sys_prompt="You are a helpful assistant. Use the ask_user tool to ask the user a question.", api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL",default="https://api.openai.com/v1"), model="gpt-4o", timeout=300.0, tools=[], reasoning=None):
    self.api_key = api_key
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
    self.tools = tools   # this is our copy
    if len(tools) > 0:   # this copy goes to the llm server
      self.req["tools"] = []
      for tl in tools:
        self.req["tools"].append(fn_to_tool_json(tl))
 
  @property
  def headers(self) -> Dict[str, str]:
    hdr =  {
      "Authorization": f"Bearer {self.api_key}",
      "Content-Type": "application/json",
      "User-Agent": "lydia/0.0.2"
    }
    x_portkey_provider = os.getenv("X_PORTKEY_PROVIDER",default=None)
    if x_portkey_provider is not None:
      hdr["x-portkey-provider"] = x_portkey_provider
    return hdr

  def req_single(self,user_input=None):
    global MAX_RETRY
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

  def req_loop(self,user_input):
    global DEBUG_REQUESTS
    RETN_DATA = None
    RETN_TOOL = False
    last_user_input = user_input
    while True:
      if RETN_DATA is not None and RETN_TOOL is False:
        return RETN_DATA
      elif RETN_DATA is not None and RETN_TOOL is True:
        print(RETN_DATA)
      RETN_DATA = None
      RETN_TOOL = False
      resp = self.req_single(last_user_input) 
      last_user_input = None
      if DEBUG_REQUESTS:
        print("<<<" * 10)
        print(json.dumps(resp.json(),indent=2))
        print("<<<" * 10)
      outputs = resp.json()["output"]
      for resp_obj in outputs:
        if resp_obj["type"] == "function_call":
          RETN_TOOL = True
          fn_obj = None
          for i in self.tools:
            if i.__name__ == resp_obj["name"]:
              fn_obj = i
              break
          if fn_obj is None:
            print("fatal: could not execute call '%s'" %  resp_obj["name"])
            return "fatal: could not execute call '%s'" % resp_obj["name"]
          fn_args = json.loads(resp_obj["arguments"])
          respval = fn_obj(**fn_args)
          self.req["input"].append({
            "arguments":resp_obj["arguments"],
            "call_id":resp_obj["id"],
            "name":resp_obj["name"],
            "type":"function_call",
            "status":"completed"
          })
          self.req["input"].append({
            "call_id":resp_obj["id"],
            "output":respval,
            "type":"function_call_output",
          })
        elif resp_obj["type"] == "message":
          # do not return if we also have a tool call
          RETN_DATA = resp_obj["content"][0]["text"]
          # return resp_obj["content"][0]["text"]
        elif resp_obj["type"] == "reasoning":
          print("Thinking...")
        else:
          print("fatal: don't know how to handle response object type '%s'" % resp_obj["type"])
          sys.exit(-1)

if __name__ == "__main__":
  a = Agent(tools=[ask_user])
  data = a.req_loop("Write a poem about fruit. Ask the user what type of fruit.") 
  print(data)  
