# Lydia - MCP Support

### Problem

Many tools are exposed to AI (OpenCode, Claude Code, etc) via the MCP standard. Lydia should optionally support this standard, while adhering to it's design philosophy of intentional friction and user control.

To support this, we implement core/mcp.py, with the primary interface being MCPLoader.
