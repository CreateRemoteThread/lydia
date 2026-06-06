#!/usr/bin/env python3

import tools.filetool
import tools.vmtool
import tools.minibrowser
import tools.term
import tools.chrome
import tools.debug

class ToolLoader:
  def registerHatchery(self,hatch_name):
    print("info: registering hatch '%s'" % hatch_name)
    if hatch_name in self.tools.keys():
      print("warning: ToolLoader trying to register '%s' as hatchery, already loaded" % name)
    else:
      self.tools[hatch_name] = lambda input_str: self.run_hatch(hatch_name,input_str)
      self.tools[hatch_name].__name__ = hatch_name
      self.tools[hatch_name].__doc__ = "Call the hatchery '%s'" % hatch_name
      self.tooldesc[hatch_name] = ""

  def registerFunction(self,name,function,func_desc):
    if name in self.tools.keys():
      print("warning: ToolLoader trying to register '%s', already loaded" % name)
    else:
      self.tools[name] = function
      self.tools[name].__doc__ = func_desc
      self.tooldesc[name] = func_desc
 
  def run_hatch(self,hatch_name,input_str):
    print("info: ToolLoader calling run_hatch(%s,%s)" % (hatch_name,input_str))
    return "ok"
 
  def __init__(self):
    self.hatcherystore = {}
    self.tools = {}
    self.tooldesc = {}
    self.registerFunction("file_rg",filetool.file_rg, "Find files using rg.")
    self.registerFunction("file_read",filetool.file_read, "Read a file.")
    self.registerFunction("file_write",filetool.file_write, "Write to a file.")
    self.registerFunction("file_glob",filetool.file_glob, "Find files using glob.")
    self.registerFunction("shell_exec",vmtool.shell_exec, "Run a non-interactive shell process.")
    self.registerFunction("shell_interactive_start",vmtool.shell_interactive_start, "Start an interactive shell process.")
    self.registerFunction("shell_interactive_read",vmtool.shell_interactive_read, "Read from the interactive process.")
    self.registerFunction("shell_interactive_write",vmtool.shell_interactive_write, "Write to the interactive process.")
    self.registerFunction("shell_interactive_kill",vmtool.shell_interactive_kill, "Terminate the interactive process")
    self.registerFunction("web_request",minibrowser.web_request, "Make a web request.")
    self.registerFunction("web_download_file",minibrowser.web_download_file, "Download a file.")
    self.registerFunction("term_start",term.term_start, "Start an interactive process.")
    self.registerFunction("term_screen_scrape",term.term_screen_scrape, "Read the process terminal.")
    self.registerFunction("term_locatechr",term.term_locatechr, "Locate a character on the screen.")
    self.registerFunction("term_interact",term.term_interact, "Write to the interactive process.")
    self.registerFunction("term_kill",term.term_kill, "Terminate the interactive process.")
    self.registerFunction("chrome_debug",chrome.devtools, "Send a request to a Chrome DevTools server at http://localhost:9222/ .")
    self.registerFunction("debug_print",debug.debug_print, "Print a debugging message.")

  def fetch_toolbox(self,name):
    out = []
    for i in self.tools.keys():
      if i.startswith(name):
        out.append(i)
    print("info: fetch_toolbox(%s) returned %d results" % (name,len(out)))
    return out

  def fetch(self,name):
    print("info: attempting to grab tool '%s'" % name)
    if name.startswith("hatch:"):
      shortname = name[6:]
      if shortname in self.tools.keys():
        return self.tools[shortname]
      else:
        print("info: detected hatchery-as-tool pattern, passing")
        self.registerHatchery(shortname)
        return self.tools[shortname]
    else:
      if name in self.tools.keys():
        return self.tools[name]
      else:
        print("warning: ToolLoader cannot fetch '%s', not found" % name)
        return None
