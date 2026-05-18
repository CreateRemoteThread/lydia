#!/usr/bin/env python3

import asyncio
from typing import Annotated
import sys
import os
import time
from os.path import expanduser, normpath
import subprocess
import queue, threading

VM_SSHARGS = os.getenv("VM_SSHARGS",default=None)
# pseudomutex: just hold the process here.
PROCESS_LOCK = None
PROCESS_RD_QUEUE = None
PROCESS_RD_THREAD = None

def async_reader(pipe, q):
  global PROCESS_RD_QUEUE
  for line in iter(pipe.readline, ''):
    PROCESS_RD_QUEUE.put(line)

def shell_exec(command: Annotated[str, "The command to run"]):
  global VM_SSHARGS
  if VM_SSHARGS is None:
    print("fatal: you must specify VM_SSHARGS to use shell_exec")
    sys.exit(-1)
  if VM_SSHARGS.startswith("ssh ") is False:
    print("fatal: don't run local commands from ai you fucking retard")
    sys.exit(-1)
  command = command.replace("'", "\\'")
  command = command.replace("*", "\\*")
  new_c = VM_SSHARGS + " '" + command + "'"
  print("info: shell_exec('%s') called" % new_c)
  result = subprocess.run(new_c, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
  return result.stdout

def shell_interactive_start(command: Annotated[str, "The command to run"]):
  global VM_SSHARGS, PROCESS_LOCK, PROCESS_RD_QUEUE, PROCESS_RD_THREAD
  if VM_SSHARGS is None:
    print("fatal: you must specify VM_SSHARGS to use shell_exec")
    sys.exit(-1)
  if VM_SSHARGS.startswith("ssh ") is False:
    print("fatal: don't run local commands from ai you fucking retard")
    sys.exit(-1)
  if PROCESS_LOCK is not None:
    print("warn: shell_interactive_start called with PROCESS_LOCK on")
    return "error: you can only have one interactive process at a time"
  # command = command.replace("'", "\\'")
  # command = command.replace("*", "\\*")
  # new_c = VM_SSHARGS + " '" + command + "'"
  print("info: shell_interactive_start('%s') called, locking pretend mutex" % command)
  PROCESS_LOCK = subprocess.Popen(
    VM_SSHARGS.split() + [command],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
  )
  print("info: starting async read queue")
  PROCESS_RD_QUEUE = queue.Queue()
  PROCESS_RD_THREAD = threading.Thread(
    target=async_reader,
    args=(PROCESS_LOCK.stdout, PROCESS_RD_QUEUE),
    daemon=True
  )
  PROCESS_RD_THREAD.start()
  return "ok"

def shell_interactive_read():
  global PROCESS_LOCK, PROCESS_RD_QUEUE,PROCESS_RD_THREAD
  if PROCESS_LOCK is None:
    print("warn: shell_interactive_read called without PROCESS_LOCK")
    return "error: you have not started an interactive process"
  out = ""
  time.sleep(2.0)
  while True:
    try:
      line = PROCESS_RD_QUEUE.get(timeout=2)
      out += line
    except queue.Empty:
      break
  if len(out) == 0:
    print("returning nothing")
    return "got no output"
  else:
    print("returning something")
    return "got output:\n %s" % out

def shell_interactive_write(data: Annotated[str, "The data to write"]):
  global PROCESS_LOCK, PROCESS_RD_QUEUE,PROCESS_RD_THREAD
  if PROCESS_LOCK is None:
    print("warn: shell_interactive_write called without PROCESS_LOCK")
    return "error: you have not started an interactive process"
  PROCESS_LOCK.stdin.write(data.rstrip() + "\n")
  PROCESS_LOCK.stdin.flush()
  return "ok"

