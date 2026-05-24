#!/usr/bin/env python3

import sys
import os
import core.agent
import core.memory
import json
import uuid
import jinja2
import tools
from typing import Annotated

# -design note-
# We can use tools to deterministically force a choice between known
# nodes/tools (i.e. offload error checking to the provider). However,
# we can also just check the LLM's output. Experimenting with the second
# path.
def node_route(tag,fruit_count: Annotated[int, "The number of fruits"]):
  print("special: node_route called with tag '%s', fruit count is %d" % (tag, fruit_count))
  return "ok"

class Drone(core.agent.Agent):
  def __init__(self,node_name,sys_prompt,usr_prompt,_tools=[],next=None,model=None):
    print("drone: initializing drone '%s'" % node_name)
    self.toolbox = tools.ToolLoader()
    self.name = node_name
    self.usr_prompt = usr_prompt
    self.next = next
    self.avail_tools = []
    self.save_output = None
    self.write_output = None
    self.preserve_ctx = False
    # -design note-
    # it's tempting to just allow toolbox fetching, but this puts us
    # in an awkward position with file_write. in practice, there is no
    # good way to force models to use file_write appropriately - so
    # just don't allow fetch_toolbox("file")
    for t in _tools:
      self.avail_tools.append(t)
      # self.avail_tools.append(self.toolbox.fetch(t))
    super().__init__(sys_prompt=sys_prompt + "\n" + self.toolbox.prompthelper(self.avail_tools),tools=[self.toolbox.fetch(t) for t in self.avail_tools],model=model)
    # super().append_tagged_tool(node_route,"Drone","Use node_route-Drone when needed")

  def run(self,ctx):
    super().flush_history()
    template = jinja2.Template(self.usr_prompt)
    new_usr_prompt = template.render(ctx=ctx)
    return super().req_loop(new_usr_prompt)

class Hatchery:
  def __init__(self, fn):
    self.nodes = {}
    with open(fn) as f:
      self.nodegraph = json.loads(f.read())
    self.start = self.nodegraph["start"]
    user_inputs = self.nodegraph.get("inputs",{})
    file_inputs = self.nodegraph.get("readfiles",{})
    self.ctx = {}
    for i in user_inputs.keys():
      self.ctx[i] = input(user_inputs[i]).strip()  
    for i in file_inputs.keys():
      with open(file_inputs[i],"r") as f:
        self.ctx[i] = f.read()
      self.ctx[i] = input(user_inputs[i]).strip()  
    for node in self.nodegraph["nodes"]:
      node_model =  node.get("model",os.getenv("OPENAI_DEFAULT_MODEL","gpt-4o"))
      node_name =  node.get("name","%s" % uuid.uuid4())
      sys_prompt = node.get("sys_prompt","You are a helpful assistant.")
      usr_prompt = node["usr_prompt"]
      tools  = node.get("tools",[])
      self.nodes[node_name] = Drone(node_name,sys_prompt,usr_prompt,tools,next=node.get("next",None),model=node_model)
      self.nodes[node_name].save_output = node.get("save_output",None)
      self.nodes[node_name].write_output = node.get("write_output",None)
    print("hatchery: init ok with %d nodes" % len(self.nodes.keys()))

  def run(self,ctx=None):
    if ctx is not None:
      ctx_grafted = 0
      ctx_collided = 0
      for i in ctx.keys():
        if i not in self.ctx.keys():
          self.ctx[i] = ctx[i]
          ctx_grafted += 1
        else:
          print("hatchery: ctx.%s collided during graft, using own" % i)
          ctx_collided += 1
      print("hatchery: run() called with ctx graft, %d grafted, %d collided" % (ctx_grafted, ctx_collided))
      self.ctx = ctx
    else:
      print("hatchery: run() called with no context")
    drone = self.nodes[self.start]
    while True:
      output = drone.run(self.ctx)
      if drone.save_output is not None:
        self.ctx[drone.save_output] = output
      if drone.write_output is not None:
        with open(drone.write_output,"w") as f:
          f.write(output)
        # self.ctx[drone.save_output] = output
      if drone.next is None:
        print(output)
        break
      elif isinstance(drone.next,list):
        # select one only.
        if len(drone.next) == 0:
          print("fatal: drone '%s' has an empty nextlist")
          sys.exit(-1)
        if len(drone.next) == 1:
          print("hatchery: drone '%s' nextlist contains one item, routing to '%s'" % (drone.name,drone.next[0]))
          drone = self.nodes[drone.next[0]]
          continue
        for i in drone.next[:-1]:
          if i in output:
            print("hatchery: passing from '%s' to '%s'" % (drone.name,i))
            drone = self.nodes[i]
        print("hatchery: passing from '%s' to default route '%s'" % (drone.name,drone.next[-1]))
        drone = self.nodes[drone.next[-1]]
        continue
      else:
        print("hatchery: passing from '%s' to '%s'" % (drone.name, drone.next))
        drone = self.nodes[drone.next]
        continue
      
