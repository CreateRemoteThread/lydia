# Lydia - Memory Handling

The primary consumer of tokens is memory - old tool calls, old outputs, admin fluff. Lydia handles this by assigning tool calls a configurable MEMORY_DECAY env var (defaulting to 6). This is implemented in core.memory.

The effect is:
- Tool calls which are over MEMORY_DECAY turns will vanish out of memory.
- While the history is longer than 3 * MEMORY_DECAY:
  - Delete the first turn after the system prompt (both query and response)
- The second behaviour can be disabled with CONSECRATE_MEMORY=adsf

Consider raising MEMORY_DECAY for tasks which require more information, but may not require tool calls.

The following commands can interact with memory while in interactive (-i) mode:

```
- !reset: flush memory completely, waiting for next user input
- !stats: check the size of memory
- !save <filename>: save context to file as JSON
- !load <filename>: load JSON-dumped context from file
```
