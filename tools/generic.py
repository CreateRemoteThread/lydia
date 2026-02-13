#!/usr/bin/env python3

import os
import subprocess

class FSExplorer:
  def __init__(self, initPath):
    self.initPath = os.path.realpath(os.path.expanduser(initPath))
    print("FSExplorer: set initPath to %s" % self.initPath)

  def constrain_path(self,dir):
    print("FSExplorer: constrain_path on %s" % dir)
    temp_path = os.path.realpath(os.path.expanduser(self.initPath + "/" + dir))
    if temp_path.startswith(self.initPath) is False:
      print("error: %s is outside %s" % (temp_path,self.initPath))
      return False
    else:
      return temp_path

  def get_strings(self,filename):
    print("FSExplorer: get_strings on %s" % filename)
    tp = self.constrain_path(filename)
    if tp is not False:
      if os.path.isfile(tp):
        result = subprocess.run(["strings","-n8",tp],check=True,text=True,capture_output=True)
      else:
        return "error: %s is not a file" % tp
    else:
      return "error: get_strings failed (no permission)"

  def list_directory_contents(self,directory):
    print("FSExplorer: list_directory on %s" % directory)
    tp = self.constrain_path(directory)
    if tp is not False:
      if os.path.islink(tp):
        result = subprocess.run(["ls","-lahL",tp],check=True,text=True,capture_output=True)
      else:
        result = subprocess.run(["ls","-lah",tp],check=True,text=True,capture_output=True)
      print(result.stdout)
      return result.stdout
    else:
      return "error: list_directory_contents failed (no permission)"

  def get_filetype(self,filename):
    print("FSExplorer: get_filetype on %s" % filename)
    tp = self.constrain_path(filename)
    if tp is not False:
      result = subprocess.run(["file",tp],check=True,text=True,capture_output=True)
      return result.stdout
    else:
      return "error: get_filetype failed (no permission)"

if __name__ == "__main__":
  print("error: you shouldn't run this directly.")
