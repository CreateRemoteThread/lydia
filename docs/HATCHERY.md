# Lydia - Hatchery Mode

### Problem

It is not reasonable to implement a complex workflow using a single instance of core.agent.Agent and one req_loop call, no matter how complex the prompting and toolset, or "how reasoning" the model is.

Therefore, it is critical to build a way for agent instances to pass content to one another.

### Architecture

A Hatchery object represents a network of Baneling() or Drone(core.agent.Agent) objects ("nodes"), as described in a configuration JSON file (see hatchery/*).

- A Baneling object is a static tool call.
- A Drone object is an LLM inference call.

Each node must implement:

- node.run(self,ctx)
- node.next
- node.save_output
- node.write_output

A drone can specify one or more "next" nodes:

- If a drone has zero next nodes (i.e. next is not present): hatchery will print the output of that drone and exit.
- If a drone has exactly one next node: hatchery will run the next drone.
- If a drone has more than one next node: hatchery will check the output of the current drone. If any of the next node names are present, it will route to that drone. If not, it will route to the last node as a default case. (todo: consider changing).

Output can be passed between nodes, using a shared context object which exists for the lifetime of the hatchery ("ctx"). Write to the output of ctx with "save_output", read from it with Jinja2 templating (ctx.varnamehere).

### Hatchery-as-Tool / Agent-as-Tool

Fundamentally, there should be no difference (to the LLM) between invoking an MCP, a hatchery, another agent or a regular function - all of these are functions. Therefore, an arbirary hatchery can be included as a tool. To do this, simply include a tool using this syntax:

```
hatch:hatchery/bananwriter.json
```

This will expose a single tool, according to the JSON "name" and "desc" properties. This function takes a single string (saved in the context as "input". The output of the final node is taken as the hatchery-tool's output.

### Reading material

- [colony_agent](https://github.com/qriousec/colony_agent)
- [google multi agent patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [patch diffing and llms](https://www.clearseclabs.com/blog/patch-diffing-llms-ghidriff-obts-2025/)
