#!/usr/bin/env python3

# This code demonstrates deterministic control of sub-agents, regardless of model.
# Invoke this with lydia --mcp workers.py -p "Call create_threads"

import threading

agentObj = None

def _load_pytool(agent):
  global agentObj
  agentObj = agent
  agent.mcploader.blacklist("print_hello")

def print_hello():
  global agentObj
  a = agentObj.duplicate()
  print(a.req_loop("Write a short story about a fruit"))
  return

def create_threads():
  threads = []
  for _ in range(3):
    thread = threading.Thread(target=print_hello)
    threads.append(thread)
    thread.start()

  for thread in threads:
    thread.join()
