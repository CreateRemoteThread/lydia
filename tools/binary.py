#!/usr/bin/env python3

import lief
import os
import sys

class BinaryTool:
  def __init__(self,bin_name,path_scope=None):
    if path_scope is None:
      raise "exception: BinaryTool without path_scope is unsafe, bye"
    if path_scope is "":
      print("warning: path_scope is blank, will always pass")
    self.bin_name = os.path.realpath(bin_name)
    if not self.bin_name.startswith(path_scope):
      raise "exception: BinaryTool created for file not in scope"
    self.binary = lief.parse(self.bin_name)

  def get_imports(self):
    imports = []
    for func in self.binary.imported_functions:
      imports.append(func.name)
    return " ".join(imports)

if __name__ == "__main__":
  bt = BinaryTool(sys.argv[1],sys.argv[1])
  bt.get_imports()

