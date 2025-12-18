"""Defines the main 'discovery_coordinator' agent."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from . import prompt
from .specialists.compound_analyzer import agent as compound_analyzer_agent
from .specialists.literature_researcher import agent as literature_researcher_agent
from .specialists.infrastructure_specialist import agent as infrastructure_specialist_agent

# Standardizing on the high-reasoning model
MODEL = "gemini-2.5-pro"

# Define the Agent directly
discovery_coordinator = LlmAgent(
    name="discovery_coordinator",
    model=MODEL,
    description="The main agent that coordinates drug discovery tasks.",
    instruction=prompt.DISCOVERY_COORDINATOR_PROMPT,
    tools=[
        AgentTool(agent=compound_analyzer_agent.compound_analyzer),
        AgentTool(agent=literature_researcher_agent.literature_researcher),
        AgentTool(agent=infrastructure_specialist_agent.infrastructure_specialist),
    ],
)

# Export the NATIVE ADK agent. 
# This ensures Vertex AI detects the framework as "google-adk".
root_agent = discovery_coordinator