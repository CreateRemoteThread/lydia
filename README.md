# lydia

This is an extremely bare-bones tool, meant for interfacing with LLM's while keeping the token count down, and providing granular visibility / customisation around tool calls.

Use the following command line args:
```
- -i/--interactive: interactive mode (i.e. chat interface)
- -p/--prompt: set the prompt
- -m/--model: set the model
- -t/--tool: load a single tool
- -r/--reasoning <low/medium/high>: enable reasoning where available.
- --toolbox <name>: load a set of tools that start with name
- --persona <persona/name.md>: replace system prompt with persona
```

You can set the following environment variables:
```
- OPENAI_BASE_URL
- OPENAI_API_KEY
- DEBUG_REQUESTS (set to any value to enable dumping requests)
- X_PORTKEY_PROVIDER (if you're using portkey)
- FN_SANDBOX (set to absolute path, file operations are constrained here)
- VM_SSHARGS (set to ssh lol@lolhost, this prefixes any shell_exec commands)
- I_ACCEPT_THE_RISK (set to "ISO27001" to run commands locally, overrides VM_SSHARGS)
```

To add a new tool:
- Write the code in the tools/ directory
- Register it in tools/__init__.py (in ToolLoader.__init__)

You probably shouldn't be here, you probably want /r/vibecoding instead.
