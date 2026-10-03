#!/usr/bin/env python3

from pathlib import Path
import os
import re
import sys
import core.config

GLOBAL_FN_PREFIX = None

def is_path_safe(test_path):
  global GLOBAL_FN_PREFIX
  if GLOBAL_FN_PREFIX is None:
    print("sbx: initializing...")
    global_path = core.config.getenv("FN_PREFIX",default="")
    GLOBAL_FN_PREFIX = global_path.split(",")
    cur_path = Path(".").resolve()
    usr_path = Path(os.path.expanduser("~")).resolve()
    if cur_path == usr_path:
      x = input("sbx: allow lydia access to homedir? [risk_accepted/*] > ").rstrip()
      if x != "risk_accepted":
        print("sbx: exit, user did not explicitly accept the risk of running in homedir")
        sys.exit(0)
    else:
      x = input("sbx: do you trust '%s'? [y/*] > " % cur_path).rstrip()
      if x != "y":
        print("sbx: exit, user did not confirm sandbox trust")
        sys.exit(0)
  sandbox_paths = [".","/var/tmp","/tmp","/private/tmp"] + GLOBAL_FN_PREFIX
  if "$" in test_path:
    print("sbx: is_path_safe('%s'), rejecting because of '$'" % test_path)
    return False
  try:
    p = Path(os.path.expanduser(test_path))
    path1 = p.resolve()
  except:
    print("sbx: is_path_safe('%s'), rejecting because Path cast failed" % test_path)
    return False
  for sbx_path in sandbox_paths:
    path_parent = Path(sbx_path).resolve()
    try:
      path1.relative_to(path_parent)
      print("sbx: '%s' is subdir of '%s', ok" % (test_path,sbx_path))
      return str(path1)
    except ValueError as e:
      continue
  return False

if __name__ == "__main__":
  print("tester")
  while True:
    testpath = input( " > ").strip()
    if is_path_safe(testpath) is not False:
      print("OK")
    else:
      print("NO")
 
