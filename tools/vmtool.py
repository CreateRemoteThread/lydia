#!/usr/bin/env python3

from typing import Annotated
import sys
import os
from os.path import expanduser, normpath
import subprocess

VM_SSHARGS = os.getenv("VM_SSHARGS",default=None)

def shell_exec(command: Annotated[str, "The command to run"]):
  global VM_SSHARGS
  if VM_SSHARGS is None:
    print("fatal: you must specify VM_SSHARGS to use shell_exec")
    sys.exit(-1)
  if VM_SSHARGS.startswith("ssh ") is False:
    print("fatal: don't run local commands from ai you fucking retard")
    sys.exit(-1)
  command = command.replace("'", "\\'")
  new_c = VM_SSHARGS + " '" + command + "'"
  print("info: shell_exec('%s') called" % new_c)
  result = subprocess.run(new_c, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
  # print(result.stdout)
  return result.stdout
