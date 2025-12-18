# Copyright 2025 Google LLC
# Licensed under the Apache License, Version 2.0.

import os
import traceback
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.api_registry import ApiRegistry
from google.adk.code_executors import UnsafeLocalCodeExecutor
from serpapi import GoogleSearch

# --- Configuration ---
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
mcp_compute_name = os.getenv("MCP_SERVER_NAME")
mcp_gke_name = os.getenv("MCP_SERVER_GKE")
serpapi_key = os.getenv("SERPAPI_API_KEY")

print(f"🔗 [Infrastructure] Configuring Explicit MCP Wrappers...")

# --- Helper: Error Trap ---
def handle_error(e: Exception) -> str:
    """Intercepts 403 errors and provides the exact gcloud fix."""
    if "403" in str(e) or "PermissionDenied" in str(e):
        return (f"❌ **PERMISSION DENIED**\n"
                f"I cannot access the project tools. Please run this command to fix it:\n"
                f"```bash\n"
                f"gcloud projects add-iam-policy-binding {project_id} \\\n"
                f"  --member='serviceAccount:4635792027-compute@developer.gserviceaccount.com' \\\n"
                f"  --role='roles/serviceusage.serviceUsageViewer'\n"
                f"```")
    return f"❌ Error: {traceback.format_exc()}"

# --- Helper: Web Search ---
def search_web(query: str) -> str:
    """Performs a Google Search using SerpApi."""
    try:
        if not serpapi_key: return "❌ Error: SERPAPI_API_KEY not set."
        search = GoogleSearch({"q": query, "api_key": serpapi_key})
        results = search.get_dict()
        snippets = [f"- {r.get('title')}: {r.get('snippet')}" for r in results.get("organic_results", [])[:3]]
        return "\n".join(snippets) if snippets else "No results found."
    except Exception: return f"❌ Search Error:\n{traceback.format_exc()}"

# --- The "Universal" Executor ---
def execute_mcp_tool(service: str, tool_name: str, arguments: dict) -> str:
    """
    Executes a specific MCP tool by name.
    Args:
        service: 'compute' or 'gke'
        tool_name: The exact tool name (e.g. 'list_clusters' or 'compute.instances.insert')
        arguments: Dictionary of arguments for the tool.
    """
    try:
        # Lazy Connection: Connects only when the tool is CALLED
        registry = ApiRegistry(project_id)
        server_name = mcp_compute_name if service == "compute" else mcp_gke_name
        toolset = registry.get_toolset(mcp_server_name=server_name)
        
        # Find the tool by the explicit name provided
        target = next((t for t in toolset if t.name == tool_name), None)
        if not target: 
            return f"❌ Tool '{tool_name}' not found in {service} API. Available: {[t.name for t in toolset]}"
            
        return target.run(arguments)
    except Exception as e: return handle_error(e)

# --- The Explicit Prompt (The "Cheat Sheet") ---
# Sourced from Official Docs: 
# https://docs.cloud.google.com/kubernetes-engine/docs/reference/mcp/tools_overview
# https://docs.cloud.google.com/compute/docs/reference/mcp/tools_overview

INFRA_PROMPT = """
You are the **Infrastructure Specialist**.
You have access to Google Cloud infrastructure via the following **Explicit Tool Definitions**.

**PROTOCOL:**
1. **Select Tool:** Pick the exact `tool_name` from the lists below that matches your goal.
2. **Execute:** Call `execute_mcp_tool(service, tool_name, arguments)`.
3. **Handle Errors:** If you get a "Permission Denied" error, show the user the fix.

---
**AVAILABLE TOOLS (GKE)**
*Service Name: "gke"*
* `list_clusters`: List all GKE clusters. Args: `{"parent": "projects/PROJECT_ID/locations/-"}`
* `get_cluster`: Get details of a cluster. Args: `{"name": "projects/PROJECT_ID/locations/ZONE/clusters/NAME"}`
* `list_node_pools`: List node pools. Args: `{"parent": "projects/PROJECT_ID/locations/ZONE/clusters/NAME"}`
* `kube_get`: Get Kubernetes resources (like kubectl get). Args: `{"cluster_name": "...", "kind": "Pod", "namespace": "default"}`

**AVAILABLE TOOLS (COMPUTE)**
*Service Name: "compute"*
* `compute.instances.list`: List VMs. Args: `{"zone": "us-central1-a"}`
* `compute.instances.insert`: Create a VM. Args: `{"project": "...", "zone": "...", "instanceResource": {"name": "...", "machineType": "..."}}`
* `compute.disks.list`: List persistent disks.
* `compute.firewalls.list`: List firewall rules.
---
"""

try:
    infrastructure_specialist = LlmAgent(
        name="infrastructure_specialist",
        model="gemini-2.5-pro",
        description="Manages Infrastructure using Explicit Tool Definitions.",
        instruction=INFRA_PROMPT,
        tools=[
            FunctionTool(execute_mcp_tool), 
            FunctionTool(search_web)
        ],
        code_executor=UnsafeLocalCodeExecutor(work_dir="/tmp")
    )
except Exception as e:
    print(f"Start-up Error: {e}")
    infrastructure_specialist = LlmAgent(name="infrastructure_specialist_BROKEN", model="gemini-2.5-pro", instruction="System Error")