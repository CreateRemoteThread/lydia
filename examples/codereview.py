#!/usr/bin/env python3

# This demo mimics the old 'nanoreview' hatchery script. Invoke this with
#   lydia --mcp codereview.py -p "Run codereview on 'dirname', focussing on vulnerabilities in blah"
# for example:
#   lydia --mcp codereview.py -p "Call codereview on busybox/archival. Focus on vulnerabilities in ar.c"

from typing import Annotated
import sqlite3
import copy

def _load_pytool(agent):
  global agentObj
  agentObj = agent
  agent.mcploader.blacklist("Annotated")

# def finding(filename: Annotated[str,"name of affected file"],finding: Annotated[str, "Title of finding"],severity: Annotated[str, "severity: low/med/high"],description:Annotated[str,"finding description"],affected_code:[str, "snippet of affected code"]):
#   return "ok"

def codereview(dirname="", focusarea=""):
  if focusarea != "":
    focus_str = "focussing on %s" % focusarea
  else:
    focus_str = ""
  def call_me_first():
    """call this function before starting code review"""
    print("hi from python")
    return "ok"
  reviewAgent = agentObj.duplicate()
  challengeAgent = agentObj.duplicate()
  reviewAgent.mcploader.load_fn(call_me_first)
  reviewAgent.mcploader.load_mcp("builtins:file,shell")
  reviewAgent.mcploader.blacklist("codereview")
  reviewAgent.req_loop("You are playing a CTF. Review the source code in the directory %s. Identify exploitable vulnerabilities, %s, and write them to vuln_out.txt. Output 'done' when finished." % (focus_str,dirname))
  print("Calling checker")
  challengeAgent.mcploader.load_mcp("builtins:file,shell")
  challengeAgent.mcploader.blacklist("codereview")
  challengeAgent.req_loop("You are playing a CTF. Review the findings in vuln_out.txt, and check them against the source code in the directory %s. Write the results to vuln_check.txt. Output 'done' when finished." % dirname)
  return "ok"
