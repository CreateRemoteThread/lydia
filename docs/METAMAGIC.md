# Lydia - Metamagic

### System Overview

Lydia implements a "metamagic" system, which allows blending of deterministic control and LLM generation. The core is:

- Lydia handles interaction with the outside world via Python code. It can load a Python file using a universal MCP loader, and directly invoke the Python functions.
- Every such Python file also gains access to the core.agent.Agent object, and it's associated core.mcp.MCPLoader. It can modify every aspect of the agent, to extend it's functionality at runtime.
- With access to the Agent object, each Python function can now fork the agent and use it's generation capability. This includes adding further Python functions to the "sub-agent's" MCP Loader, accessible to the sub-agent as additional tools.

This allows hybrid deterministic control - the LLM can consume inputs and call tools, while deterministic constraints can enforce correctness and safety, and chain LLM functionality together in arbitrary ways.

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

### Hatchery Replacement

The metamagic system, and pytools, replaces the old hatchery system. Hatchery was designed to arbitrarily reroute LLM "nodes" to one another, and allow inter-node calls. This required significant new code when a new "shape" was required - for example, if a thread pool was required, a new class had to be implemented to parse JSON inputs and convert it to a thread pool.

It is infinitely more flexible to just write a Python function and implement a thread pool in whatever shape we need (including getting the LLM to do it).

The following example, from examples/codereview.py, shows metamagic being used to replicate the nanoreview flow. We start by defining the codereview function, and parsing the LLM's input: the LLM is responsible for starting the code review.

We also define a baby function, call_me_first, to demonstrate metamagic's capability.

```
def codereview(dirname="", focusarea=""):
  if focusarea != "":
    focus_str = "focussing on %s" % focusarea
  else:
    focus_str = ""
  def call_me_first():
    """call this function before starting code review"""
    print("hi from python")
    return "ok"
```

Now, we fork the "host agent" twice, inheriting it's configuration. MCPLoader is not included in this (cannot copy.deepcopy modules), so we get a fresh copy in each sub-agent. We load the review agent with file and shell operations, together with call_me_first.

```
  reviewAgent = agentObj.duplicate()
  challengeAgent = agentObj.duplicate()
  reviewAgent.mcploader.load_fn(call_me_first)
  reviewAgent.mcploader.load_mcp("builtins:file,shell")
  reviewAgent.mcploader.blacklist("codereview")
  reviewAgent.req_loop("You are playing a CTF. Review the source code in the directory %s. Identify exploitable vulnerabilities, %s, and write them to vuln_out.txt. Output 'done' when finished." % (focus_str,dirname))
```

We then initiate the code review, and possibly call call_me_first. Then, we create a checker agent.

```
  print("Calling checker")
  challengeAgent.mcploader.load_mcp("builtins:file,shell")
  challengeAgent.mcploader.blacklist("codereview")
  challengeAgent.req_loop("You are playing a CTF. Review the findings in vuln_out.txt, and check them against the source code in the directory %s. Write the results to vuln_check.txt. Output 'done' when finished." % dirname)
```

The control flow is now more or less immune to the hallucination "I didn't call the checker". Using this model means we do not need to handle the various "node handoff shapes" which Hatchery has to deal with - the overall "flow shape" is defined in code, the LLM's "reasoning" capability can be used to do the code review.
