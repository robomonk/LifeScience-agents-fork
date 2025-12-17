# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP storage bucket for staging.")
flags.DEFINE_bool("create", False, "Creates a new agent.")
flags.DEFINE_bool("list", False, "Lists all agents.")

# --- 1. DEFINE THE INPUT SCHEMA (Universal Receptor) ---
class AgentInput(BaseModel):
    # Validates that 'input' must be a string
    input: str = Field(..., description="The user's natural language query.")
    
    # CRITICAL: This line tells Pydantic to silently accept ANY other 
    # arguments Gemini sends (user_id, model parameters, etc.) 
    # instead of rejecting them.
    model_config = ConfigDict(extra='allow')

# --- 2. THE TYPED ENGINE ---
class DrugDiscoveryTypedEngine:
    def __init__(self):
        print("Typed Engine Initialized")

    # INTERNAL TOOLS
    def _search_pubchem(self, query):
        import pubchempy as pcp
        try:
            compounds = pcp.get_compounds(query, 'name')
            if not compounds:
                return f"No matches found for '{query}'"
            c = compounds[0]
            return (f"Name: {c.synonyms[0] if c.synonyms else query}\n"
                    f"CID: {c.cid}\n"
                    f"Formula: {c.molecular_formula}\n"
                    f"Weight: {c.molecular_weight}")
        except Exception as e:
            return f"PubChem Error: {str(e)}"

    def _search_pubmed_rest(self, query):
        import requests
        import xml.etree.ElementTree as ET
        try:
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax=3&usehistory=y"
            r = requests.get(search_url)
            root = ET.fromstring(r.text)
            id_list = [id_elem.text for id_elem in root.findall(".//Id")]
            if not id_list:
                return "No articles found."
            ids = ",".join(id_list)
            fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={ids}&retmode=text&rettype=abstract"
            r_fetch = requests.get(fetch_url)
            return f"PubMed Results:\n{r_fetch.text[:1000]}..." 
        except Exception as e:
            return f"PubMed/Network Error: {str(e)}"

    def _run_logic(self, query_text: str) -> str:
        """Shared logic processing."""
        input_lower = query_text.lower()
        response = []
        response.append(f"🤖 Processing: {query_text}")

        if "pubchem" in input_lower or "structure" in input_lower or "weight" in input_lower:
            term = query_text.split(" ")[-1].strip("?") 
            response.append(f"   --> Tool Call: PubChem Search for '{term}'")
            result = self._search_pubchem(term)
            response.append(f"   --> Result: {result}")
        elif "pubmed" in input_lower or "paper" in input_lower or "cancer" in input_lower:
            term = query_text.replace("search pubmed for", "").strip()
            response.append(f"   --> Tool Call: PubMed Search for '{term}'")
            result = self._search_pubmed_rest(term)
            response.append(f"   --> Result: {result}")
        else:
            response.append("   --> logic: General query.")
            response.append("   --> Answer: I can search PubChem (structures) and PubMed (papers).")
        
        return "\n".join(response)

    # --- 3. THE STRICT API METHODS ---
    
    def query(self, input: AgentInput) -> str:
        """Synchronous Query with Strict Typing."""
        return self._run_logic(input.input)

    # Note: We don't strictly need stream_query if we have strict typing, 
    # but if Gemini insists on it, we can add it back. 
    # For now, let's try just 'query' with the correct schema.

def create_agent():
    AGENT_NAME = "agentic-tx"
    
    try:
        agents = agent_engines.list()
        for agent in agents:
            if agent.display_name == AGENT_NAME:
                print(f"Deleting old agent: {agent.resource_name}")
                agent.delete(force=True)
    except:
        pass

    print(f"🚀 Deploying TYPED AGENT: {AGENT_NAME}...")
    
    remote_agent = agent_engines.create(
        DrugDiscoveryTypedEngine(),
        display_name=AGENT_NAME,
        requirements=[
            "google-cloud-aiplatform==1.131.0",
            "pydantic==2.11.7",
            "cloudpickle==3.1.1",
            "pubchempy>=1.0.4",
            "requests>=2.0.0", 
        ],
    )
    print(f"✅ Created remote agent: {remote_agent.resource_name}")

def main(_):
    load_dotenv()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    
    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")

    if FLAGS.create:
        create_agent()

if __name__ == "__main__":
    app.run(main)