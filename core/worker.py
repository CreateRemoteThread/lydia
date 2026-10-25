#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, wait
from typing import Annotated

pool = ThreadPoolExecutor()
workers = []
worker_output = []
AgentClass = None

def __init_workers(agent):
  global AgentClass
  print("worker: prepping agent class")
  AgentClass = agent

def core_worker(prompt):
  global AgentClass, worker_output
  a = AgentClass.duplicate()
  a.flush_history()
  worker_output.append(a.req_loop(prompt))

def create_worker(prompt: Annotated[str, "prompt to pass to worker"]):
  """create a worker, based on a prompt, for an asynchronous task. get the result with wait_worker"""
  global pool, workers
  future = pool.submit(core_worker,prompt)
  print("worker: '%s'" % prompt)
  workers.append(future)
  return "ok"

def wait_worker():
  """wait for all workers to complete, return the result"""
  global workers, worker_output
  if len(workers) == 0:
    return "failed: no running workers"
  already_waiting = True
  wait(workers)
  print("worker: ok, all workers returned")
  workers.clear()
  output = ""
  for w in worker_output:
    output += "Agent returned: %s" % w
    output += "\n"
  return output
