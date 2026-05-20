# Lydia - Memory Handling

### Problem

The primary consumer of tokens is memory - old tool calls, old outputs, admin fluff. Lydia handles this by assigning tool calls a configurable MEMORY_DELAY env var (defaulting to 6).

Consider raising this for complex tasks (or maybe not forcing a random token generator to complete complex tasks? idk).

The following commands can interact with memory while in interactive (-i) mode:

```
- !reset: flush memory completely, waiting for next user input
- !stats: check the size of memory
- !save <filename>: save context to file as JSON
- !load <filename>: load JSON-dumped context from file
```
