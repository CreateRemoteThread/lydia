#!/usr/bin/env python3

from typing import Annotated
import sys
import os
from os.path import expanduser, normpath
from agents import Agent, Runner, function_tool
import r2pipe
import lief

R2_CLIENT = None
FN_PREFIX = os.getenv("FN_SANDBOX",default=None)
if FN_PREFIX is not None:
  FN_PREFIX = expanduser(normpath(FN_PREFIX))

def r2_init(filename: Annotated[str,"The name of the file to analyze"]):
  global R2_CLIENT, FN_PREFIX
  if FN_PREFIX is None:
    print("fatal: you must set FN_SANDBOX")
    sys.exit(-1)
  real_name = expanduser(normpath(filename))
  if real_name.startswith(FN_PREFIX) is False:
    print("info: r2init converting relative path to real path")
    real_name = expanduser(normpath(FN_PREFIX + "/" + real_name))
  if os.path.isfile(real_name) is False:
    print("error: '%s' is not a real file" % real_name)
    return "error: could not open '%s'" % real_name
  print("info: r2init called on '%s'" % real_name)
  R2_CLIENT = r2pipe.open(real_name)
  return "ok"


def r2_cmd(command: Annotated[str,"The command to run"]):
  global R2_CLIENT
  if R2_CLIENT is None:
    print("error: call r2init first")
    return "error: use the r2init tool to initialize"
  if command.strip().startswith("!"):
    print("error: command '%s' refused, no shell commands" % command)
    return "refused by security policy"
  print("info: r2cmd('%s')" % command)
  data = R2_CLIENT.cmd(command)
  return data
