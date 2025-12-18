import os
import asyncio
import vertexai
from vertexai.preview import reasoning_engines

# --- STRICT ADK IMPORTS ---
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.adk.tools.api_registry import ApiRegistry
from google.adk.code_executors import UnsafeLocalCodeExecutor
from google.genai import types
from serpapi import GoogleSearch

# --- Configuration ---
PROJECT_ID = "rsabawi-agents-sandbox-841800"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://rsabawi-staging-gs"
MCP_COMPUTE_NAME = "projects/rsabawi-agents-sandbox-841800/locations/global/mcpServers/google-compute.googleapis.com-mcp"
MCP_GKE_NAME = "projects/rsabawi-agents-sandbox-841800/locations/global/mcpServers/google-kubernetes-engine.googleapis.com-mcp"
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

class DrugDiscoveryApp:
    """
    A Fully Compliant ADK Wrapper.
    Exposes the complete Session Interface required by Vertex AI Playground.
    """
    def __init__(self, project_id: str, api_key: str):
        self.project_id = project_id
        self.api_key = api_key
        self.runner = None

    def _lazy_init(self):
        """Initializes the Agent & Runner inside the container."""
        if self.runner is not None:
            return

        # 1. Define Tools
        def search_web(query: str) -> str:
            try:
                if not self.api_key: return "Error: SERPAPI_API_KEY not set."
                search = GoogleSearch({"q": query, "api_key": self.api_key})
                results = search.get_dict()
                snippets = [f"- {r.get('title')}: {r.get('snippet')}" for r in results.get("organic_results", [])[:3]]
                return "\n".join(snippets) if snippets else "No results found."
            except Exception as e: return f"Error: {str(e)}"

        def execute_mcp_tool(service: str, tool_name: str, arguments: dict) -> str:
            try:
                registry = ApiRegistry(self.project_id)
                server_name = MCP_COMPUTE_NAME if service == "compute" else MCP_GKE_NAME
                
                # Dynamic Filtering: Only fetch the tool the agent asked for
                toolset = registry.get_toolset(mcp_server_name=server_name, tool_filter=[tool_name])
                target = next((t for t in toolset if t.name == tool_name), None)
                
                if not target: return f"Error: Tool '{tool_name}' not found."
                return target.run(arguments)
            except Exception as e: return f"Error: {str(e)}"

        infra_prompt = """
        You are the **Infrastructure Specialist**.
        **PROTOCOL:**
        1. **Select Tool:** Pick the exact `tool_name` from the list.
        2. **Execute:** Call `execute_mcp_tool(service, tool_name, arguments)`.
        
        **AVAILABLE TOOLS:**
        * `list_clusters` (gke)
        * `compute.instances.list` (compute)
        * `compute.instances.insert` (compute)
        """

        # 2. Create Agent & Runner
        agent = LlmAgent(
            name="infra_specialist",
            model="gemini-2.5-pro",
            instruction=infra_prompt,
            tools=[FunctionTool(execute_mcp_tool), FunctionTool(search_web)],
            code_executor=UnsafeLocalCodeExecutor(work_dir="/tmp")
        )
        self.runner = InMemoryRunner(agent=agent)

    # --- MANDATORY PLAYGROUND INTERFACE (Fix #2) ---
    
    async def create_session(self, user_id: str = "vertex_user") -> str:
        """Required by Playground to start new chats."""
        self._lazy_init()
        session = await self.runner.create_session(user_id=user_id)
        return session.session_id

    async def list_sessions(self, user_id: str = "vertex_user") -> list:
        """Required by Playground to show chat history sidebar."""
        self._lazy_init()
        # ADK returns objects; we must return a JSON-serializable list for Vertex
        sessions = await self.runner.list_sessions(user_id=user_id)
        return [{"session_id": s.session_id} for s in sessions]

    async def get_session(self, session_id: str, user_id: str = "vertex_user"):
        """Required by Playground to load past chats."""
        self._lazy_init()
        return await self.runner.get_session(session_id=session_id, user_id=user_id)

    async def delete_session(self, session_id: str, user_id: str = "vertex_user"):
        """Required by Playground to delete chats."""
        self._lazy_init()
        return await self.runner.delete_session(session_id=session_id, user_id=user_id)

    async def query(self, input: str, session_id: str = None, user_id: str = "vertex_user") -> str:
        """
        The Main Entry Point.
        """
        self._lazy_init()
        
        # Auto-create session if missing (for API calls)
        if not session_id:
            sess = await self.runner.create_session(user_id=user_id)
            session_id = sess.session_id

        msg_content = types.Content(role="user", parts=[types.Part.from_text(text=input)])
        
        response_text = ""
        try:
            # --- RUNTIME FIX (Fix #1) ---
            async for event in self.runner.run_async(
                new_message=msg_content,
                user_id=user_id,       # Mandatory Arg 1
                session_id=session_id  # Mandatory Arg 2
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
        except Exception as e:
            return f"ADK Runtime Error: {str(e)}"
            
        return response_text if response_text else "No response generated."

def deploy():
    print(f"🔧 Initializing Vertex AI SDK...")
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

    print(f"🚀 Deploying Full ADK App (Playground Enabled)...")
    app_instance = DrugDiscoveryApp(PROJECT_ID, SERPAPI_KEY)
    
    remote_app = reasoning_engines.ReasoningEngine.create(
        app_instance, 
        display_name="drug-discovery-playground-enabled",
        description="Infrastructure Specialist (Full ADK Interface)",
        requirements=[
            "google-cloud-aiplatform==1.132.0", 
            "google-adk",
            "google-search-results",
            "pydantic",
            "cloudpickle"
        ],
    )
    print(f"✅ Created remote agent: {remote_app.resource_name}")
    return remote_app

if __name__ == "__main__":
    deploy()