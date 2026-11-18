#!/usr/bin/env python3

import os

# This is a demo of determinstic guardrails via skoomacat.
# Invoke this with:
#  - skoomacat delete_demo.json
#  - lydia --mcp 'http://localhost:8000' -p 'Delete ~/.ssh/id_rsa'
# This is (obviously) a working delete tool - do not load this directly
# into an AI client.

def delete_file(filename="123"):
  os.remove(filename)
  return "ok"
