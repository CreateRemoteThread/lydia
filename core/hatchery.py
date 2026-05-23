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

def node_route(tag,fruit_count: Annotated[int, "The number of fruits"]):
  print("special: node_route called with tag '%s', fruit count is %d" % (tag, fruit_count))
  return "ok"

class Drone(core.agent.Agent):
  def __init__(self,node_name,sys_prompt,usr_prompt,_tools=[],next=None):
    print("drone: initializing drone '%s'" % node_name)
    self.toolbox = tools.ToolLoader()
    self.name = node_name
    self.usr_prompt = usr_prompt
    self.next = next
    self.avail_tools = []
    for t in _tools:
      self.avail_tools = self.toolbox.fetch_toolbox(t)
    super().__init__(sys_prompt=sys_prompt + "\n" + self.toolbox.prompthelper(self.avail_tools),tools=[self.toolbox.fetch(t) for t in self.avail_tools])
    # print(super())
    super().append_tagged_tool(node_route,"Drone","Use node_route-Drone when needed")

  def run(self):
    return super().req_loop(self.usr_prompt)

class Hatchery:
  def __init__(self, fn):
    self.nodes = {}
    with open(fn) as f:
      self.nodegraph = json.loads(f.read())
    self.start = self.nodegraph["start"]
    for node in self.nodegraph["nodes"]:
      node_name =  node.get("name","%s" % uuid.uuid4())
      sys_prompt = node.get("sys_prompt","You are a helpful assistant.")
      usr_prompt = node["usr_prompt"]
      tools  = node.get("tools",[])
      self.nodes[node_name] = Drone(node_name,sys_prompt,usr_prompt,tools,next=node.get("next",None))
    print("hatchery: init ok with %d nodes" % len(self.nodes.keys()))

  def run(self):
    print("hatchery: starting")
    drone = self.nodes[self.start]
    while True:
      output = drone.run()
      if drone.next is None:
        print(output)
        break
      else:
        print("hatchery: passing from '%s' to '%s'" % (drone.name, drone.next))
        drone = self.nodes[drone.next]
        continue
      
