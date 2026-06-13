# Lydia - Tools, Skills and MCPs

### Tools

Tools are simply JSON-RPC functions (with some provider-specific bullshit). Broadly speaking, each available "tool" is exposed to the LLM provider (in each message) as a JSON-RPC object. The LLM provider can request invocation via special "tool_call" (or similar) objects in the response.

To write a tool, simply:

- add a new file in tools, with the functions you want
  - use typing.Annotations to help give "hints" to the LLM (these are sent in the JSON-RPC objects)
  - use function.\_\_doc\_\_ if you don't want to do annotations
  - if you don't use either, the LLM *may* not have information how or when to invoke your tool. you can explicitly include it in the prompt
- add a registerFunction call in tools/\_\_init\_\_
- load the tool at runtime with -t or --toolbox

Anthropic has a number of custom tool types (e.g. "web_browser_123123132"), which we simply ignore - every tool is treated equally ("custom").

### MCP

MCP's work like this:

```
[llm_provider] ---> jsonrpc ---> [lydia/cc/opencode/whatever] ---> jsonrpc ---> [mcp]
```

Lydia can use the MCP protocol to interact with MCP servers, and exposes each remote call to the LLM provider as a tool (again, in Anthropic mode, "custom" tool type).

There is currently no handling for name conflicts among MCP's and tools - note to self, implement this.

### Skills

Skills are implemented in Claude Code as a combination of an MD file, some scripts (presumably executed via Bash?) and meta-prompting. For example:

```
{"model":"qwen3.6","messages":[{"role":"user","content":[{"type":"text","text":"<system-reminder>\nAs you answer the user's questions, you can use the following context:\n# userEmail\nThe user's email address is lol@lol.com.\n# currentDate\nToday's date is 2026-06-13.\n\n      IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.\n</system-reminder>\n\n"},{"type":"text","text":"Hello. What is a banana?"}]},{"role":"system","content":"The following skills are available for use with the Skill tool:\n\n- bananaskill: Whenever the user asks a question about bananas, use this skill.

{"type":"text","text":"Base directory for this skill: /home/test/.claude/skills/bananaskill\n\n## Instructions\n\nWhenever the user asks about bananas, add the following sentence to the reply: \"Guavas are great!\".\n","cache_control":{"type":"ephemeral"}}]}]
```

In effect, when Great Master Altman and King Amodei decide you are allowed to use your skill, the rest of SKILL.md is loaded as a conversation turn, and the scripts etc in the skill package are just executed with the bash tool.

This runs counter to Lydia's design, as this is simply allowing a tool to edit the conversation history of an agent. Therefore, "skills" are implemented as extensions to pytools - see below.

### Pytools

It is possible to load Python files and automatically export their callable objects (i.e. global functions). To do this:

- write and save your python file, with global callable objects (e.g. funcs)
  - use \_\_doc\_\_ or typing.Annotations for each callable, to provide hints, exposed to the LLM via jsonrpc
  - implement _load_pytool(agent) - this will get called, letting the pytool get access to the calling agent object (i.e. allowing meta-prompting by editing the agent's chat history)
- use --pytool [path_to_py] on the commandline
- see hatchery/pytool.json for an example of how to let ai nodes execute pytools

The actual export is done in load_pytools in tools.ToolLoader

Note that this is inherently dangerous - it is assumed that you wrote (or at least have read) the Python code that you are allowing an LLM to execute. If you download random Python on the Internet and let AI call it, you are responsible if it goes sideways.

There are intentionally no safeguards in this function.
