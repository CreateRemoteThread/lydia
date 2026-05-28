# Lydia - MCP Support

### Problem

Many tools are exposed to AI (OpenCode, Claude Code, etc) via the MCP standard. Lydia should optionally support this standard, while adhering to it's design philosophy of intentional friction and user control.

### Implementation

To support this, we implement core/mcp.py, with the primary interface being MCPLoader: a core.agent.Agent is expected to have one MCPLoader, which handles *all* connected MCP servers.

Only stdio is supported right now.

There is no support for starting new MCP servers or terminating them - you start them with the process (cmdline or eventually hatchery), and they die on process exit.
