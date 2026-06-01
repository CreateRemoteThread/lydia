#!/usr/bin/env python3

import sys
import os
from typing import Annotated
if os.getenv("OFF_WITH_HER_HEAD",default=None) is None:
  from core.agent import Agent
else:
  from core.messaging import Agent
import core.memory
import core.hatchery
import core.mcp
import tools
import getopt
import readline

def ask_user(question: Annotated[str, "The question to ask"]):
  return input(question + " > ").strip()

Toolbox = tools.ToolLoader()
MCPLoader = core.mcp.MCPLoader()

def loadTool(toolName):
  global Toolbox
  r = Toolbox.fetch(toolName)
  if r is None:
    print("fatal: could not load tool '%s'" % toolName)
    sys.exit(-1)
  else:
    return r

def loadPrompt(prompt):
  return prompt
  # if os.path.isfile(prompt):
  #   with open(prompt,"r") as f:
  #     try:
  #       print("loading prompt from %s" % prompt)
  #       return f.read()
  #     except:
  #       print("fatal: cannot open or read %s" % prompt)
  #       sys.exit(-1)
  # else:
  #   return prompt

def main():
  global Toolbox
  CFG_INTERACTIVE = False
  CFG_USR_PROMPT = None
  CFG_PERSONALITY = "You are a helpful assistant."
  CFG_SYS_PROMPT = "Use the ask_user tool to ask the user a question."
  CFG_TOOLS = []
  CFG_MODEL = os.getenv("OPENAI_DEFAULT_MODEL",default="gpt-4.1-mini-2025-04-14")
  CFG_REASONING = None
  CFG_HATCHERY = None
  args,extra = getopt.getopt(sys.argv[1:],"ip:s:t:m:r:a:",["interactive","prompt=","system=","tool=","model=","reasoning=","persona=","toolbox=","agentic=","mcp="])
  for arg,val in args:
    if arg in ["-p","--prompt"]:
      CFG_USR_PROMPT = loadPrompt(val)
    elif arg in ["-i","--interactive"]:
      CFG_INTERACTIVE = True
    elif arg == "--mcp":
      MCPLoader.load_mcp(val)
    elif arg in ["-a","--agentic"]:
      CFG_HATCHERY = val
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
  if CFG_HATCHERY is not None:
    print("hatchery: passing to core.hatchery. bye!")
    h = core.hatchery.Hatchery(CFG_HATCHERY)
    h.run()
    sys.exit(0)
  got_riskaccept =  os.getenv("I_ACCEPT_THE_RISK",default=None)
  got_cmdfw = os.getenv("CMD_FW",default=None)
  got_vmsshargs = os.getenv("VM_SSHARGS",default=None)
  if (got_riskaccept is not None or got_cmdfw is not None or got_vmsshargs is not None) and len(CFG_TOOLS) == 0:
    print("fatal: tool safety constraints enabled, but 0 tools selected")
    sys.exit(-1)
  real_sys_prompt = " ".join([CFG_PERSONALITY,CFG_SYS_PROMPT])
  agent = Agent(sys_prompt=real_sys_prompt,tools=[loadTool(v) for v in CFG_TOOLS] + [ask_user],model=CFG_MODEL,reasoning=CFG_REASONING)
  agent.set_mcploader(MCPLoader)
  if CFG_USR_PROMPT is None:
    if CFG_INTERACTIVE is False:
      print("fatal: you must at least a user prompt with -p or use -i for interactive")
      sys.exit(-1)
    else:
      print("info: -i set, asking user for initial prompt")
      CFG_USR_PROMPT = input(" > ").rstrip()
      if CFG_USR_PROMPT.startswith("!"):
        print("fatal: you cannot use core.memory.memory_dispatch with 0 memory")
        sys.exit(-1)
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
      if result is not None: # don't print the result on !reset
        print(result)
      new_prompt = input(" > ").rstrip() 
      if new_prompt in ["/exit","/quit",":wq",":q","quit()","q"]:
        break
      if new_prompt.startswith("!"):    # special utility function.
        core.memory.memory_dispatch(new_prompt[1:], agent) 
        result = None
        continue
      else:
        result = agent.req_loop(new_prompt)
    print("Bye!")

if __name__ == "__main__":
  main()
