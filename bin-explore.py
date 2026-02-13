#!/usr/bin/env python3

from typing import Annotated
import r2pipe
import lief
import sys
import os

from openai import OpenAI
import asyncio
from agents import Agent, Runner, function_tool

be = None

class BinaryExplorer:
  def __init__(self, bin_name):
    real_name = os.path.realpath(os.path.realpath(bin_name))
    if os.path.isfile(real_name) is False:
      print("fatal: %s is not a file" % real_name)
      sys.exit(0)
    self.r2 = r2pipe.open(bin_name)
    self.r2.cmd("aaaa")

  def do_r2(self,cmd):
    data = self.r2.cmd(cmd)
    print(data)
    return data

@function_tool
def r2cmd(cmd: Annotated[str, "The r2 command to run"]):
  """Run a radare2 command, and get the result

  Args:
    cmd: The command to run
  """
  global be
  print(cmd)
  if cmd.strip().startswith("!"):
    return "refused by security policy"
  return be.do_r2(cmd.strip())

with open("prompts/bin_explorer_sys") as f:
  sys_prompt = f.read()

r2agent = Agent(
  name="r2 Agent",
  instructions=sys_prompt,
  tools=[r2cmd],
)

async def do_cmd(cmd):
  global r2agent
  result = await Runner.run(r2agent, input=cmd, max_turns=50)
  print(result.final_output)
 
if __name__ == "__main__":
  if len(sys.argv) != 2:
    print("fatal: you must supply a filename")
    sys.exit(0)
  be = BinaryExplorer(sys.argv[1])
  while True:
    i = input(" > ").rstrip()
    tokens = i.split()
    if tokens[0] == "q":
      print("bye")
      break
    elif tokens[0] == "!":
      print("raw execute: %s" % " ".join(tokens[1:]))
      be.do_r2(" ".join(tokens[1:]))
    else:
      asyncio.run(do_cmd(i))
