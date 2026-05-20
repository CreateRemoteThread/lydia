#!/usr/bin/env python3

import tools.filetool
import tools.vmtool
import tools.minibrowser
import tools.term

class ToolLoader:
  def registerFunction(self,name,function,func_desc):
    if name in self.tools.keys():
      print("warning: ToolLoader trying to register '%s', already loaded" % name)
    else: 
      self.tools[name] = function
      self.tooldesc[name] = func_desc
  
  def __init__(self):
    self.tools = {}
    self.tooldesc = {}
    self.registerFunction("file_read",filetool.file_read, "Use file_read tool to read files.")
    self.registerFunction("file_write",filetool.file_write, "Use file_write tool to write files.")
    self.registerFunction("file_glob",filetool.file_glob, "Use file_glob tool to search for files.")
    self.registerFunction("shell_exec",vmtool.shell_exec, "Use shell_exec to run a non-interactive shell process.")
    self.registerFunction("shell_interactive_start",vmtool.shell_interactive_start, "Use shell_interactive_start to start an interactive shell process.")
    self.registerFunction("shell_interactive_read",vmtool.shell_interactive_read, "Use shell_interactive_read to read from the interactive process.")
    self.registerFunction("shell_interactive_write",vmtool.shell_interactive_write, "Use shell_interactive_write to write to the interactive process.")
    self.registerFunction("shell_interactive_kill",vmtool.shell_interactive_kill, "Use shell_interactive_kill to terminate the interactive process")
    self.registerFunction("web_request",minibrowser.web_request, "Use web_request to make a web request.")
    self.registerFunction("web_download_file",minibrowser.web_download_file, "Use web_download_file to download a file.")
    self.registerFunction("term_start",term.term_start, "Use term_start to start an interactive process.")
    self.registerFunction("term_screen_scrape",term.term_screen_scrape, "Use term_screen_scrape to read the process terminal.")
    self.registerFunction("term_interact",term.term_interact, "Use term_interact to write to the interactive process.")
    self.registerFunction("term_kill",term.term_kill, "Use term_kill to terminate the interactive process")

  def fetch_toolbox(self,name):
    out = []
    for i in self.tools.keys():
      if name in i:
        out.append(i)
    print("info: fetch_toolbox(%s) returned %d results" % (name,len(out)))
    return out

  def fetch(self,name):
    print("info: attempting to grab tool '%s'" % name)
    if name in self.tools.keys():
      return self.tools[name]
    else:
      print("warning: ToolLoader cannot fetch '%s', not found" % name)
      return None

  def prompthelper(self,toolnames):
    if len(toolnames) == 0:
      return ""
    else:
      return " ".join([self.tooldesc[name] for name in toolnames])
