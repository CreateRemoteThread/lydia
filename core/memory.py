#!/usr/bin/env python3 

import copy
import os
import json
import random
import string
import core.config

MEMORY_FADE = {}
TURNS_KEPT = None

def try_get_callid(evt):
  if "call_id" in evt.keys():    # openai / responses
    return evt["call_id"]
  elif "content" in evt.keys():  # anthropic / messaging
    evc = evt["content"][0]
    # print(evt["content"])
    if evc["type"] == "tool_use":
      return evc["id"] 
    elif evc["type"] == "tool_result":
      return evc["tool_use_id"] 
  else:
    return None

def memory_fade(input_array):
  pass
  # while len(input_array) != 0:
  #   del(input_array[0])  

def memory_fade_gradual(input_array):
  global MEMORY_FADE, TURNS_KEPT
  memories_purged = 0
  if TURNS_KEPT is None:
    TURNS_KEPT = core.config.getenv("TURNS_KEPT",default="6")
    TURNS_KEPT = int(TURNS_KEPT)
  if TURNS_KEPT != -1:
    del_hdr = 0
    while del_hdr < len(input_array):
      evt = input_array[del_hdr]
      call_id = try_get_callid(evt)
      if call_id is not None:
        if call_id not in MEMORY_FADE.keys():
          MEMORY_FADE[call_id] = TURNS_KEPT
        else:
          if MEMORY_FADE[call_id] == 1:
            del(MEMORY_FADE[call_id])
            del(input_array[del_hdr])
            continue
          else:
            MEMORY_FADE[call_id] -= 1
      del_hdr += 1
  else:
    print("mem: memory_decay is -1, preserving tool calls")
  if TURNS_KEPT != -1:
    while len(input_array) > 2 * (TURNS_KEPT + 1):
      print("mem: deleting turn")
      del(input_array[1])
      del(input_array[1])
  else:
    print("mem: consecrated memory active, disabling amnesia")
  if memories_purged != 0:
    print("mem: purged %d memories from context" % memories_purged)

def do_save(input_arr,filename):
  try:
    with open(filename,"w") as f:
      f.write(json.dumps(input_arr))
    print("mem: saved context to '%s'" % filename)
  except:
    print("mem: error, could not save to '%s'" % filename)

def do_load(filename,agent):
  try:
    with open(filename,"r") as f:
      data = json.loads(f.read())
      agent.req[agent._sz_memory] = data
    print("mem: loaded context from '%s'" % filename)
  except:
    print("mem: error, could not load from '%s'" % filename)

def do_stats(input_arr):
  user_data = 0
  user_reqs = 0
  asst_data = 0
  asst_reqs = 0
  func_data = 0
  fc_ids = []
  for evt in input_arr:
    if "role" in evt.keys():   # messagees
      if evt["role"] == "user":
        user_reqs += 1
        user_data += len(evt["content"])
      elif evt["role"] == "assistant": 
        asst_reqs += 1
        asst_data += len(evt["content"])
    elif "type" in evt.keys(): # function calls / returns
      if evt["type"] in ["function_call","function_call_output"]:
        if evt["call_id"] not in fc_ids:
          fc_ids.append(evt["call_id"])
        if "output" in evt.keys():
          func_data += len(evt["output"])
      else:
        print("mem: do_stats encountered unhandled type '%s', ignoring" % evt["type"])
  print("mem: user data: %d bytes, %d requests" % (user_data,user_reqs))
  print("mem: asst data: %d bytes, %d replies" % (asst_data,asst_reqs))
  print("mem: %d unique function calls, %d bytes" % (len(fc_ids), func_data))

def memory_dispatch(cmd,agent):
  # print(agent)
  # print(agent._sz_memory)
  print("mem: handling command of '%s'" % cmd)
  tokens = cmd.split()
  if cmd == "reset" or cmd == "flush":
    agent.req[agent._sz_memory] = []
    print("memory: context reset")
  elif cmd == "stats":
    do_stats(agent.req[agent._sz_memory])
  elif tokens[0] == "save" and len(tokens) == 2:
    do_save(agent.req[agent._sz_memory],tokens[1])
  elif tokens[0] == "load" and len(tokens) == 2:
    do_load(tokens[1],agent)
  return

if __name__ == "__main__":
  print("You probably want /r/vibecoding instead")
