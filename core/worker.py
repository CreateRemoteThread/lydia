#!/usr/bin/env python3

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated

pool = ThreadPoolExecutor()
condition = threading.Condition()
workers = 0
results = []
AgentClass = None

def __init_workers(agent):
  global AgentClass
  print("worker: prepping agent class")
  AgentClass = agent

def core_worker(prompt):
  global AgentClass, worker_output
  a = AgentClass.duplicate()
  a.flush_history()
  return a.req_loop(prompt)
  # worker_output.append(a.req_loop(prompt))

def create_worker(prompt: Annotated[str, "prompt to pass to worker"], total_workers: Annotated[int, "how many total workers being created"]):
  """create a worker, based on a prompt, for an asynchronous task. get the result with wait_worker"""
  print(total_workers)
  global pool, workers, condition
  with condition:
    workers += 1
  def smallify(p):
    if len(p) < 40:
      return p
    else:
      return p[0:40] + "..."
  print("worker: created worker with prompt '%s', workers = %d" % (smallify(prompt),workers))
  def run():
    global workers, worker_out, condition
    try:
      result = core_worker(prompt)
      with condition:
        results.append(result)
    finally:
      with condition:
        # print("bye!")
        workers -= 1
        condition.notify_all()
  pool.submit(run)
  with condition:
    while workers > 0:
      condition.wait()
    output = "create_worker pool finished"
    w_count = 0
    for r in results:
      output += "worker %d returns: %s\n" % (w_count,r)
      w_count += 1
    print(output)
    # result + "\n".join(results)
    # print(result)
    return output
