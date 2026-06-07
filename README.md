# lydia

![its lydia!](docs/img/lydia.png)

Docs: [safety](docs/SAFETY.md) | [memory](docs/MEMORY.md) | [slashem](docs/SLASHEM.md) | [hatchery](docs/HATCHERY.md) | [mcp](docs/MCP.md)

This is an extremely bare-bones tool, meant for interfacing with LLM's while keeping the token count down, and providing granular visibility / customisation around tool calls.

Use the following command line args:
```
- -i/--interactive: interactive mode (i.e. chat interface)
- -p/--prompt: set the prompt
- -m/--model: set the model
- -t/--tool: load a single tool
- -r/--reasoning <low/medium/high>: enable reasoning where available. this is not always required - check your inference provider.
- -a/--agentic: experimental. load a json file for hatchery mode
- --toolbox <name>: load a set of tools that start with name
- --persona <persona/name.md>: replace system prompt with persona
```

You can set the following environment variables:
```
- STFU (set to anything to remove the ask_user tool from default context)
- MEMORY_DECAY (how many turns tool calls stay in memory)
- CMD_FW (comma-separated allowed commands for shell_ tools)
- OPENAI_BASE_URL
- OPENAI_API_KEY
- OPENAI_DEFAULT_MODEL
- DEBUG_REQUESTS (set to any value to enable dumping requests)
- X_PORTKEY_PROVIDER (if you're using portkey)
- FN_SANDBOX (set to absolute path, file operations are constrained here)
- VM_SSHARGS (set to ssh lol@lolhost, this prefixes any shell_exec commands)
- I_ACCEPT_THE_RISK (set to "ISO27001" to run commands locally, overrides VM_SSHARGS)
- YELLOW_BRICK_ROAD (set to "ISO31000" to auto-approve all commands. if you use this and ai deletes your labubus, that's on you)
- OFF_WITH_HER_HEAD (set to anything to enable experimental anthropic support. todo: tidy up code, make a new agent class to handle Anthropic API)
- ANTHROPIC_MAX_TOKENS (required by anthropic, defaults 64000)
```

To add a new tool:

```
- Write the code in the tools/ directory
- Register it in tools/__init__.py (in ToolLoader.__init__)
```

You probably shouldn't be here, you probably want /r/vibecoding instead.
