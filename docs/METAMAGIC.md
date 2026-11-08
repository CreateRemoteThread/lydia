# Lydia - Metamagic

Lydia allows pytools (well, py-mcp's) to edit it's parent agent object, and spawn new agents based off the parent. This effectively allows hybrid AI and deterministic control in a single flow.

As an example, the following binja_helper script can be used to rename all the sub_ functions in a binary (or at least attempt to):

```
#!/usr/bin/env python3

# invoke with 
# lydia --mcp binja --mcp binja_helper.py -p Use binja tools to list all functions in the open binary. Use helper_rename_function to rename all the sub_ functions -m gpt-5.4

gAgent = None

def _load_pytool(agent):
  global gAgent
  gAgent = agent

def helper_rename_function(fn_name):
  """Attempt to find the purpose of a function and rename it in binja"""
  print("GOT HELPER RENAME")
  a = gAgent.duplicate()
  a.flush_history()
  a.mcploader.blacklist("helper_rename_function")
  print(a.req_loop("Use tools determine the purpose of '%s' and rename the function." % fn_name))
  return "ok"
```

Here, the primary loop maintains a minimal context (the list of sub_ functions, and one invocation to helper_rename_function each), while "subagents" (clones of the original agent) work on the actual renaming task.

There is some "analysis tax": for example, when using this to rename a binary with a pile of plt resolver stubs, Binja will attempt to work out what the plt looks like again and again (but this still beats lugging around millions of tokens in a single thread of context, or the duct-tape of "subagents").
