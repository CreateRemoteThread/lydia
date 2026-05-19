#!/usr/bin/env python3

import sys
import os
from typing import Annotated
import core.agent
import tools
import getopt

def ask_user(question: Annotated[str, "The question to ask"]):
  return input(question + " > ").strip()

Toolbox = tools.ToolLoader()

def loadTool(toolName):
  global Toolbox
  r = Toolbox.fetch(toolName)
  if r is None:
    print("fatal: could not load tool '%s'" % toolName)
    sys.exit(-1)
  else:
    return r

def loadPrompt(prompt):
  if os.path.isfile(prompt):
    with open(prompt,"r") as f:
      try:
        print("loading prompt from %s" % prompt)
        return f.read()
      except:
        print("fatal: cannot open or read %s" % prompt)
        sys.exit(-1)
  else:
    return prompt

def main():
  global Toolbox
  CFG_INTERACTIVE = False
  CFG_USR_PROMPT = None
  CFG_PERSONALITY = "You are a helpful assistant."
  CFG_SYS_PROMPT = "Use the ask_user tool to ask the user a question."
  CFG_TOOLS = []
  CFG_MODEL = "gpt-4o"
  CFG_REASONING = None
  args,extra = getopt.getopt(sys.argv[1:],"ip:s:t:m:r:",["interactive","prompt=","system=","tool=","model=","reasoning=","persona=","toolbox="])
  for arg,val in args:
    if arg in ["-p","--prompt"]:
      CFG_USR_PROMPT = loadPrompt(val)
    elif arg in ["-i","--interactive"]:
      CFG_INTERACTIVE = True
    elif arg in ["-r","--reasoning"]:
      if val in ["low","medium","high"]:
        CFG_REASONING = val
      else:
        print("warn: r must be 'low', 'medium' or 'high' - reasoning remains None")
    elif arg in ["-s","--sysprompt"]:
      CFG_SYS_PROMPT = loadPrompt(val)
    elif arg in ["-t","--tool"]:
      CFG_TOOLS.append(val)
    elif arg == "--toolbox":
      CFG_TOOLS += Toolbox.fetch_toolbox(val)
    elif arg in ["-m","--model"]:
      CFG_MODEL = val
    elif arg == "--persona":
      print("info: loading persona '%s'" % val)
      if os.path.isfile(val):
        with open(val) as f:
          CFG_PERSONALITY = f.read()
      else:
        print("warn: cannot open persona '%s'" % val)
  real_sys_prompt = " ".join([CFG_PERSONALITY,CFG_SYS_PROMPT])
  # print(CFG_MODEL)
  agent = core.agent.Agent(sys_prompt=real_sys_prompt,tools=[loadTool(v) for v in CFG_TOOLS] + [ask_user],model=CFG_MODEL,reasoning=CFG_REASONING)
  if CFG_USR_PROMPT is None:
    if CFG_INTERACTIVE is False:
      print("fatal: you must at least a user prompt with -p or use -i for interactive")
      sys.exit(-1)
    else:
      print("info: -i set, asking user for initial prompt")
      CFG_USR_PROMPT = input(" > ").rstrip()
  if len(CFG_TOOLS) >= 1:
    print("info: using tools, attaching prompt helper string")
    CFG_USR_PROMPT += "\n" + Toolbox.prompthelper(CFG_TOOLS)
  if CFG_INTERACTIVE is False:
    result = agent.req_loop(CFG_USR_PROMPT)
    print(result)
    sys.exit(0)
  else:
    result = agent.req_loop(CFG_USR_PROMPT)
    while True:
      print(result)
      new_prompt = input(" > ").rstrip() 
      if new_prompt in ["/exit","/quit",":wq",":q","quit()"]:
        break
      result = agent.req_loop(new_prompt)
    print("Bye!")

if __name__ == "__main__":
  main()
