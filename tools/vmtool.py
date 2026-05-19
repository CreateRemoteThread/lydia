#!/usr/bin/env python3

import re
import asyncio
from typing import Annotated
import sys
import os
import time
from os.path import expanduser, normpath
import subprocess
import queue, threading

RISK_ACCEPT = os.getenv("I_ACCEPT_THE_RISK",default=None)
VM_SSHARGS = os.getenv("VM_SSHARGS",default=None)
# pseudomutex: just hold the process here.
PROCESS_LOCK = None
PROCESS_RD_QUEUE = None
PROCESS_RD_THREAD = None
PROCESS_RD_STOP = False

ANSI_ESCAPE_RE = re.compile(r"\x1B\x5B[0-9;]+m")
def strip_terminal_colors(text: str) -> str:
  return ANSI_ESCAPE_RE.sub('', text)

if RISK_ACCEPT is not None:
  if RISK_ACCEPT == "ISO27001":
    print("warn: I_ACCEPT_THE_RISK set to ISO27001, running commands locally")
    RISK_ACCEPT = True
  else:
    RISK_ACCEPT = False

CMD_FW = os.getenv("CMD_FW", default=None)
if CMD_FW is not None:
  CMD_FW = [a.strip() for a in CMD_FW.split(",")]

def cmdfw(command):
  global CMD_FW
  print("fw: firewalling '%s'" % command)
  if CMD_FW is None:
    manual_allow = input("fw: CMD_FW whitelist unset. allow this once? [y/N] > ").rstrip()
    if manual_allow == "y":
      print("fw: command manually permitted")
      return True
    print("fw: command not permitted")
    return False
  else:
    cmd0 = command.split()[0]
    if cmd0 in CMD_FW:
      print("fw: command whitelisted, allowing")
      return True
    else:
      print("fw: command not in whitelist, denying")
      return False

def fwreject():
  global CMD_FW
  if CMD_FW is None:
    return "error: permission denied by user"
  else:
    return "error: permission denied by firewall. allowed commands: %s" % " ".join(CMD_FW)

# courtesy of gpt-4o
# neat trick!
def async_reader(pipe, q):
  global PROCESS_RD_QUEUE, PROCESS_RD_STOP
  for line in iter(pipe.readline, ''):
    if PROCESS_RD_STOP is True:
      return
    PROCESS_RD_QUEUE.put(line)

def shell_exec(command: Annotated[str, "The command to run"]):
  global VM_SSHARGS, RISK_ACCEPT
  if VM_SSHARGS is None and RISK_ACCEPT is False:
    print("fatal: you must specify VM_SSHARGS to use shell_exec, or I_ACCEPT_THE_RISK to run locally")
    sys.exit(-1)
  if cmdfw(command) is False:
    return fwreject()
  if RISK_ACCEPT is True:
    print("warn: I_ACCEPT_THE_RISK detected, running shell_exec('%s') locally" % command)
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return strip_terminal_colors(result.stdout)
  else:
    if VM_SSHARGS.startswith("ssh ") is False:
      print("fatal: don't run local commands from ai you fucking retard")
      sys.exit(-1)
    command = command.replace("'", "\\'")
    command = command.replace("*", "\\*")
    new_c = VM_SSHARGS + " '" + command + "'"
    print("info: shell_exec('%s') called" % new_c)
    result = subprocess.run(new_c, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return strip_terminal_colors(result.stdout)

def shell_interactive_start(command: Annotated[str, "The command to run"]):
  global VM_SSHARGS, PROCESS_LOCK, PROCESS_RD_QUEUE, PROCESS_RD_THREAD, RISK_ACCEPT
  if VM_SSHARGS is None and RISK_ACCEPT is False:
    print("fatal: you must specify VM_SSHARGS to use shell_exec")
    sys.exit(-1)
  if PROCESS_LOCK is not None:
    print("warn: shell_interactive_start called with PROCESS_LOCK on")
    return "error: you can only have one interactive process at a time"
  if cmdfw(command) is False:
    return fwreject()
  if RISK_ACCEPT is True:
    print("warn: shell_interactive_start('%s') called, locking pretend mutex, running locally" % command)
    PROCESS_LOCK = subprocess.Popen(
      command.split(),
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True
    )
  else:
    if VM_SSHARGS.startswith("ssh ") is False:
      print("fatal: don't run local commands from ai you fucking retard")
      sys.exit(-1)
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
    print("info: shell_interactive_read returns nothing")
    return "got no output"
  else:
    new_out = strip_terminal_colors(out)
    print("info: shell_interactive_read returned %d bytes (%d stripped)" % (len(out),len(new_out)))
    return "got output:\n %s" % new_out

def shell_interactive_write(data: Annotated[str, "The data to write"]):
  global PROCESS_LOCK, PROCESS_RD_QUEUE,PROCESS_RD_THREAD
  if PROCESS_LOCK is None:
    print("warn: shell_interactive_write called without PROCESS_LOCK")
    return "error: you have not started an interactive process"
  print("info: shell_interactive_write('%s') called" % data.rstrip())
  PROCESS_LOCK.stdin.write(data.rstrip() + "\n")
  PROCESS_LOCK.stdin.flush()
  return "ok"

def shell_interactive_kill():
  global PROCESS_LOCK, PROCESS_RD_QUEUE, PROCESS_RD_THREAD, PROCESS_RD_STOP
  print("info: shell_interactive_kill() invoked")
  PROCESS_LOCK.terminate()
  PROCESS_LOCK = None
  print("info: pseudo-lock cleared")
  PROCESS_RD_QUEUE = None
  PROCESS_RD_STOP = True
  # PROCESS_RD_THREAD.stop()
  PROCESS_RD_THREAD.join()
  PROCESS_RD_STOP = False
  print("info: reader thread terminated and joined")
  return "ok, process killed"
