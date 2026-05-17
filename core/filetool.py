#!/usr/bin/env python3

from typing import Annotated
import sys
import os
from os.path import expanduser, normpath
from agents import Agent, Runner, function_tool

FN_PREFIX = os.getenv("FN_SANDBOX",default=None)
if FN_PREFIX is not None:
  FN_PREFIX = expanduser(normpath(FN_PREFIX))
else:
  print("fatal: you must specify FN_SANDBOX env")
  sys.exit(-1)

@function_tool
def file_read(filename: Annotated[str, "Name of the file to read"], start: Annotated[int, "Location to start reading from"], bytes: Annotated[int, "Number of bytes to read. Use -1 to read the whole file."]):
  global FN_PREFIX
  print("info: file_read(%s,%d,%d) called" % (filename,start,bytes))
  if FN_PREFIX is None:
    print("fatal: you must specify FN_SANDBOX env")
    sys.exit(-1)
  realpath = expanduser(normpath(filename))
  if realpath.startswith(FN_PREFIX):
    with open(realpath) as f:
      f.seek(start)
      if bytes == -1:
        print("info: file_read asked to get -1 bytes, reading all")
        data = f.read()
      else:
        data = f.read(bytes)
    if len(data) >= MAX_DATA:
      return "error: trying to return %d bytes, can only read %d at once" % (len(data),MAX_DATA)
    else:
      return data
  else:
    new_realpath = expanduser(normpath(FN_PREFIX + "/" + realpath))
    if os.path.isfile(new_realpath):
      print("info: file_read converted relative to absolute path")
      with open(realpath) as f:
        f.seek(start)
        if bytes == -1:
          print("info: file_read asked to get -1 bytes, reading all")
          data = f.read()
        else:
          data = f.read(bytes)
      if len(data) >= MAX_DATA:
        return "error: trying to return %d bytes, can only read %d at once" % (len(data),MAX_DATA)
      else:
        return data
    else:
      print("warn: read from '%s' blocked by sandbox" % filename)
      return "error: cannot read file, no permission"

@function_tool
def file_write(filename: Annotated[str, "Name of the file to write to"], data: Annotated[str, "Data to write"], append: Annotated[bool, "True to append to end of file, False to write over existing data"]):
  global FN_PREFIX
  print("info: file_write(%s,len(data)=%d) called" % (filename, len(data)))
  if FN_PREFIX is None:
    print("fatal: you must specify FN_SANDBOX env")
    sys.exit(-1)
  realpath = expanduser(normpath(filename))
  if realpath.startswith(FN_PREFIX) is False:
    print("info: file_write, prefixing path with FN_PREFIX")
    realpath = expanduser(normpath(FN_PREFIX + "/" + realpath))
  mode = "w"
  if append is True:
    mode = "a"
  with open(realpath,mode) as f:
    f.write(data)
  return None

@function_tool
def file_glob(pattern: Annotated[str, "Pattern to glob"]):
  global FN_PREFIX
  print("info: file_glob(%s) called" % pattern)
  realpath = expanduser(normpath(pattern))
  if realpath.startswith(FN_PREFIX) is False:
    print("info: file_glob, prefixing path with FN_PREFIX")
    realpath = expanduser(normpath(FN_PREFIX + "/" + realpath)) 
  return glob.glob(realpath,True)
