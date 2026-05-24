# Lydia - Hatchery Mode

### Problem

It is not reasonable to implement a complex workflow using a single instance of core.agent.Agent and one req_loop call, no matter how complex the prompting and toolset, or "how reasoning" the model is.

Therefore, it is critical to build a way for agent instances to pass content to one another. 

### Architecture

A Hatchery object represents a network of Drone(core.agent.Agent) objects, as described in a configuration JSON file (see hatchery/*). The drones should be able to pass messages in these ways:

- Drone1->Drone2 (including loops)
- Drone1->(Work by Drone2)->Drone1->Next Drone
- Drone1->CollectorFunction(Drone1.1,Drone1.2,Drone1.3)

Output can be passed between nodes, using a shared context object which exists for the lifetime of the hatchery ("ctx"). Write to the output of ctx with "save_output", read from it with Jinja2 templating (ctx.varnamehere).

- Exit node.

### Reading material

- [colony_agent](https://github.com/qriousec/colony_agent)
- [google multi agent patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
