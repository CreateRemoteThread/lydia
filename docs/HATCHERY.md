# Lydia - Hatchery Mode

### Problem

It is fundamentally inappropriate to rely on LLM technology to perform error-proof orchestration (in simpler words, LLM's cannot reliably do a for block or if statement). By extension, it is not appropriate to use LLM's to perform complex orchestration, regardless of it's "reasoning ability" or how Frontier it is.

Hatchery attempts to solve this by implementing a deterministic orchestration layer on top of AI 'nodes'. This helps us achieve reliable coverage on breadth-first tasks without relying on the LLM to do all the steps in a giga-prompt.

### Architecture

A Hatchery object represents a network of Baneling() or Drone(core.agent.Agent) objects ("nodes"), as described in a configuration JSON file (see hatchery/*).

- A Baneling object is a static tool call ("type":"tool").
- A Drone object is an LLM inference call (no type / default type).
- A Overlord object is a special node which starts every node specified in the 'children' property, and waits for them to finish. ("type":"workers"). See hatchery/bananapool.json for example.

Each node must implement:

- node.run(self,ctx)
- node.next
- node.save_output
- node.write_output

### Prompting / The 'ctx' object

In Hatchery mode, prompts are constructed using the Jinja2 templating engine - text enclosed in double curly braces are considered special. For example:

```
"prompt":"Write a story about {{ ctx.fruittype }}"
```

could be "Write a story about bananas", "write a story about guavas", etc.

Hatchery defaults to using the 'ctx' object to store variables for Jinja2. This contains:

- Things directly specified by the user, in the top-level 'input' attribute (containing a dict of varname:user_input_prompt)
- Things saved by other nodes. If a node specifies "save_output", it's text output is saved in ctx.saved_output_value
- Things read from files
  - The top-level "files" attribute (dict of varname:filename) will be read and loaded at startup
  - The special function {{ fread(filename) }} will dynamically read a file. filename can be dynamic as well (i.e. fread(ctx.blah) ok)

Note that the ctx object is persistent for the life of a hatchery object - there is no special handling for collisions or overwriting by accident (kinda like a python dict, because it is literally a python dict).

### Hatchery-as-Tool / Agent-as-Tool

Fundamentally, there should be no difference (to the LLM) between invoking an MCP, a hatchery, another agent or a regular function - all of these are functions. Therefore, an arbirary hatchery can be included as a tool. To do this, simply include a tool using this syntax:

```
hatch:hatchery/bananwriter.json
```

This will expose a single tool, according to the JSON "name" and "desc" properties. This function takes a single string (saved in the context as "input". The output of the final node is taken as the hatchery-tool's output.

### Node-as-Tool

It is also possible to load one node as a tool for another within Hatchery, using the following syntax in the hatchery JSON definition:

```
"tools":["node:SomeOtherNode"]
```

These are lazy-loaded - the first node can load the second without the second being defined, it is looked up at runtime. The first node can pass an input string to the second node, which is loaded in the second node as ctx.input (note: there is no consideration for threads).

### Reading material

- [colony_agent](https://github.com/qriousec/colony_agent)
- [google multi agent patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [patch diffing and llms](https://www.clearseclabs.com/blog/patch-diffing-llms-ghidriff-obts-2025/)
