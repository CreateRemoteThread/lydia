#!/usr/bin/env python3

import sys
import os
import asyncio
import subprocess
from openai import OpenAI
from typing import Annotated
from agents import Agent, Runner, function_tool
from tools.generic import FSExplorer
from tools.binary import BinaryTool
from pydantic import BaseModel

fsexpl = None
base_path = ""

@function_tool
def list_directory(directory: Annotated[str, "The directory to list"]):
  """List the contents of a directory.

  Args:
    directory: The name of the directory to list.
  """
  global fsexpl
  print("hitting list_directory on %s" % directory)
  return fsexpl.list_directory_contents(directory)

@function_tool
def test_filetype(filename: Annotated[str, "Test the type of this file"]):
  """Check the type of a file, using the UNIX file utility.

  Args:
    filename: The name of the file to test
  """
  global fsexpl
  print("hitting test_filetype on %s" % filename)
  return fsexpl.get_filetype(filename)

@function_tool
def get_strings(filename: Annotated[str, "Get strings from this file"]):
  """Extract strings from a file.

  Args:
    filename: The name of the file to extract strings from.
  """
  global fsexpl
  print("hitting get_strings on %s" % filename)
  return fsexpl.get_strings(filename)

@function_tool
def get_imports(filename: Annotated[str, "Get imports from this file"]):
  """List functions imported by a binary

  Args:
    filename: The name of the file to extract imports from.
  """
  print("hitting get_imports on %s" % filename)
  bt = BinaryTool(base_path + "/" + filename,base_path)
  return bt.get_imports()

with open("prompts/fs_explorer_sys") as f:
  sys_prompt = f.read()

class FileListing(BaseModel):
  results: list[str] 

agent = Agent(
  name="Filesystem Explorer",
  instructions=sys_prompt,
  tools=[list_directory,test_filetype, get_imports],
)

async def main():
  global fsexpl, base_path
  base_path = os.path.realpath(os.path.expanduser(sys.argv[1])) 
  fsexpl = FSExplorer(base_path)
  directory_listing = fsexpl.list_directory_contents(".")
  result = await Runner.run(agent, input="The directory listing is:\n\n %s" % directory_listing, max_turns=50)
  print(result.final_output)

if __name__ == "__main__":
  # while True:
  #   cmd = input(" > ").rstrip()
  asyncio.run(main())
