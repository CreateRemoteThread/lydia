# Lydia - Memory Handling

### Introduction

The greatest contributor to excess token usage is maintaining memory and tool calls across long-horizon tasks (also, "wasted" MCP calls). Lydia attempts to address this by two architectural decisions - that each "message" should be independent of previous context

Two changes are made to fix this:

