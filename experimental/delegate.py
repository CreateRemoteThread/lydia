# conflict with existing training

@function_tool
def delegate(prompt: Annotated[str, "The prompt for the subagent"], tools: Annotated[str, "A comma-separated list of tools for the new agent."]):
  print("info: delegate called")
  global Toolbox
  sys_prompt = "Use the ask_user tool to ask the user a question."
  agent = Agent(
      name="GenericSubagent",
      instructions=sys_prompt
    )
  result = Runner.run(agent, input=prompt)
  print(result.final_output)
  return result.final_output
