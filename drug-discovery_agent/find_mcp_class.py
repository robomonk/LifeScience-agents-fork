import mcp
import mcp.client.sse
import google.adk.tools.mcp_tool

print("--- MCP Root Attributes ---")
print([x for x in dir(mcp) if 'Sse' in x or 'Param' in x])

print("\n--- MCP Client SSE Attributes ---")
print([x for x in dir(mcp.client.sse) if 'Sse' in x or 'Param' in x])

print("\n--- Google ADK MCP Tool Attributes ---")
print([x for x in dir(google.adk.tools.mcp_tool) if 'Param' in x])