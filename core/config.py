#!/usr/bin/env python3

import os
import sys
import json
import sqlite3
import base64

CFG_GLOBAL = None
CFG_GLOBAL_FN = None
CFG_VAULTKEY = None

def commitcfg():
  global CFG_GLOBAL, CFG_GLOBAL_FN
  with open(CFG_GLOBAL_FN,"w") as f:
    f.write(json.dumps(CFG_GLOBAL,indent=2))
    print("cfg: committed updated to '%s'" % CFG_GLOBAL_FN)

# -design note-
# this allows a config file to override environment variables, by loading
# configs from a json file.
# this allows us to pack a file with "default ok" configs, and then set a
# bunch of settings at once using that (e.g. cc-mode.json)

def defaultcfg():
  global CFG_GLOBAL, CFG_GLOBAL_FN
  if CFG_GLOBAL is None:
    try:
      with open(os.path.expanduser("~/.lydia/default.cfg"),"r") as f:
        CFG_GLOBAL = json.loads(f.read())
        CFG_GLOBAL_FN = os.path.expanduser("~/.lydia/default.cfg")
    except Exception as e:
      print(e)
      print("cfg: no default cfg available")

def initcfg(filename):
  global CFG_GLOBAL, CFG_GLOBAL_FN
  if os.path.isfile(filename) is False:
    print("cfg: cannot load '%s', assuming empty")
    return
  with open(filename,"r") as f:
    print("cfg: loading config '%s'" % filename)
    if CFG_GLOBAL is not None:
      print("cfg: overwriting existing config")
    CFG_GLOBAL = json.loads(f.read())
    CFG_GLOBAL_FN = filename

def getcfg(varname,default=None):
  global CFG_GLOBAL
  if CFG_GLOBAL is None:
    return default
  if varname in CFG_GLOBAL.keys():
    return CFG_GLOBAL[varname]
  else:
    return default

def setenv(varname,val):
  global CFG_GLOBAL
  if CFG_GLOBAL is None:
    return False
  CFG_GLOBAL[varname] = val
  return True

def getsubvar(catname,varname,default=None):
  global CFG_GLOBAL
  if CFG_GLOBAL is None:
    return default
  if catname in CFG_GLOBAL.keys():
    try:
      return CFG_GLOBAL[catname][varname]
    except:
      return default
  else:
    return default

def setsubvar(catname,varname,value):
  global CFG_GLOBAL
  if CFG_GLOBAL is None:
    print("cfg: fatal: setsubvar('%s','%s',...) when CFG_GLOBAL is None" % (catname, varname))
    sys.exit(0) 
  if varname not in CFG_GLOBAL.keys():
    print("cfg: creating category '%s'" % catname)
    CFG_GLOBAL[catname] = {}
  CFG_GLOBAL[catname][varname] = value

def getenv(varname,default=None):
  global CFG_GLOBAL
  if CFG_GLOBAL is None:
    return os.getenv(varname,default=default)
  if varname in CFG_GLOBAL.keys():
    return CFG_GLOBAL[varname]
  else:
    return os.getenv(varname,default=default)

