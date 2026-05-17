#!/usr/bin/env python3

import inspect
from agents import function_tool
from typing import Annotated, get_args, get_origin
import requests
import json
import os
from typing import Dict

DEBUG_REQUESTS=os.getenv("DEBUG_REQUESTS",default=False)
if DEBUG_REQUESTS is not False:
  print("info: DEBUG_REQUESTS set, dumping requests and response json")
  DEBUG_REQUESTS = True

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
  def __init__(self, sys_prompt="You are a helpful assistant. Use the ask_user tool to ask the user a question.", api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL",default="https://api.openai.com/v1"), model="gpt-4o", timeout=10.0, tools=[], reasoning=None):
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
    return {
      "Authorization": f"Bearer {self.api_key}",
      "Content-Type": "application/json"
    }

  def req_single(self,user_input=None):
    if user_input is not None:
      self.req["input"].append({"content":user_input,"role":"user"})
    response = requests.post(
      f"{self.base_url}/responses",
      headers = self.headers,
      json = self.req,
      timeout = self.timeout
    )
    return response

  def req_loop(self,user_input):
    global DEBUG_REQUESTS
    last_user_input = user_input
    while True:
      if DEBUG_REQUESTS:
        print(">>>" * 10)
        print(json.dumps(self.req,indent=2))
        print(">>>" * 10)
      resp = self.req_single(last_user_input) 
      last_user_input = None
      if DEBUG_REQUESTS:
        print("<<<" * 10)
        print(json.dumps(resp.json(),indent=2))
        print("<<<" * 10)
      outputs = resp.json()["output"]
      for resp_obj in outputs:
        if resp_obj["type"] == "function_call":
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
          return resp_obj["content"][0]["text"]
        elif resp_obj["type"] == "reasoning":
          print("Thinking...")

if __name__ == "__main__":
  a = Agent(tools=[ask_user])
  data = a.req_loop("Write a poem about fruit. Ask the user what type of fruit.") 
  print(data)  
