#!/usr/bin/env python3 

import copy
import os
import json

MEMORY_FADE = {}
MEMORY_DECAY = os.getenv("MEMORY_DECAY",default="6")
MEMORY_DECAY = int(MEMORY_DECAY)

# called every 'turn' to flush old tool calls from memory.
def memory_fade(input_array):
  global MEMORY_FADE, MEMORY_DECAY
  for evt in input_array:
    if "call_id" in evt.keys():
      call_id = evt["call_id"]
      if call_id not in MEMORY_FADE.keys():
        # print("mem: adding new memory: '%s'" % call_id)
        MEMORY_FADE[call_id] = MEMORY_DECAY
      else:
        if MEMORY_FADE[call_id] == 0:
          # print("mem: purging call '%s' from context" % call_id)
          del(evt)
          continue
        else:
          MEMORY_FADE[call_id] -= 1
  # cannot pass by ref (cannot modify list while it's being checked)
  fl = [x for x in MEMORY_FADE.keys()]
  memories_purged = 0
  for i in fl:
    if MEMORY_FADE[i] == 0:
      memories_purged += 1
      # print("mem: purging call '%s' from context / memory" % i)
      del(MEMORY_FADE[i])
  if memories_purged != 0:
    print("mem: purged %d memories from context" % memories_purged)

def do_save(input_arr,filename):
  with open(filename,"w") as f:
    f.write(json.dumps(input_arr))
  print("mem: saved context to '%s'" % filename)

def do_load(filename,agent):
  with open(filename,"r") as f:
    data = json.loads(f.read())
    agent.req["input"] = data
  print("mem: loaded context from '%s' % filename)

def do_stats(input_arr):
  for i in input_arr:
    print(i)

def memory_dispatch(cmd,agent):
  print("memory: handling command of '%s'" % cmd)
  tokens = cmd.split()
  if cmd == "reset":
    agent.req["input"] = []
    print("memory: context reset")
  elif cmd == "stats":
    do_stats(agent.req["input"])
  return

if __name__ == "__main__":
  print("You probably want /r/vibecoding instead")
