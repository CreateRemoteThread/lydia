#!/usr/bin/env python3

def do_stats(input_arr):
  for i in input_arr:
    print(i)

def memory_dispatch(cmd,agent):
  print("memory: handling command of '%s'" % cmd)
  tokens = cmd.split()
  if cmd == "reset":
    agent.req["input"] = []
    print("memory: context reset")
  elif cmd == "stats":
    do_stats(agent.req["input"])
  return

if __name__ == "__main__":
  print("You probably want /r/vibecoding instead")
