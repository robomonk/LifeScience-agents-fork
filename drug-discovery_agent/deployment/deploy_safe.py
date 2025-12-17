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

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP storage bucket for staging.")
flags.DEFINE_bool("create", False, "Creates a new agent.")
flags.DEFINE_bool("list", False, "Lists all agents.")

# --- THE SAFE AGENT ENGINE ---
# We define the logic INSIDE this class to avoid external file dependencies.
class DrugDiscoverySafeEngine:
    def __init__(self):
        print("Safe Engine Initialized")

    def search_pubchem(self, query):
        """Tool: Search PubChem for a compound."""
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

    def fetch_pubmed(self, query):
        """Tool: Search PubMed for articles."""
        from Bio import Entrez
        Entrez.email = "rsabawi@google.com" # Hardcoded for safety
        try:
            handle = Entrez.esearch(db="pubmed", term=query, retmax=3)
            record = Entrez.read(handle)
            handle.close()
            id_list = record["IdList"]
            
            if not id_list:
                return "No articles found."
                
            # Fetch details
            handle = Entrez.efetch(db="pubmed", id=",".join(id_list), rettype="medline", retmode="text")
            records = handle.read()
            handle.close()
            return f"PubMed Results:\n{records[:500]}..." # Truncate for brevity
        except Exception as e:
            return f"PubMed Error: {str(e)}"

    def query(self, input: str) -> str:
        """
        Main Agent Logic (ReAct Loop Mock).
        """
        # LAZY IMPORT: Ensures container starts even if libraries have issues
        try:
            import requests
            import pubchempy
            import Bio
        except ImportError as e:
            return f"❌ CRITICAL: Library missing in cloud: {e}"

        input_lower = input.lower()
        response = []

        response.append(f"🤖 Processing Query: {input}")

        # Simple Router Logic (Replacing the complex ReAct loop for stability)
        if "pubchem" in input_lower or "structure" in input_lower or "weight" in input_lower or "formula" in input_lower:
            # Extract basic term (naive extraction)
            term = input.split(" ")[-1].strip("?") 
            response.append(f"   --> Tool Call: PubChem Search for '{term}'")
            result = self.search_pubchem(term)
            response.append(f"   --> Result: {result}")
        
        elif "pubmed" in input_lower or "paper" in input_lower or "research" in input_lower:
            term = input.replace("search pubmed for", "").strip()
            response.append(f"   --> Tool Call: PubMed Search for '{term}'")
            result = self.fetch_pubmed(term)
            response.append(f"   --> Result: {result}")
            
        else:
            response.append("   --> logic: General query (No specific tool triggered)")
            response.append(f"   --> Answer: I am the Drug Discovery Agent. I can search PubChem and PubMed. Try asking: 'Get structure of aspirin'")

        return "\n".join(response)

def create_agent():
    AGENT_NAME = "agentic-tx"
    
    # 1. Cleanup
    try:
        agents = agent_engines.list()
        for agent in agents:
            if agent.display_name == AGENT_NAME:
                print(f"Deleting old agent: {agent.resource_name}")
                agent.delete(force=True)
    except:
        pass

    # 2. Deploy
    print(f"🚀 Deploying SAFE AGENT: {AGENT_NAME}...")
    
    remote_agent = agent_engines.create(
        DrugDiscoverySafeEngine(),
        display_name=AGENT_NAME,
        requirements=[
            # SYSTEM (Pinned from Echo Success)
            "google-cloud-aiplatform==1.131.0",
            "pydantic==2.11.7",
            "cloudpickle==3.1.1",
            
            # AGENT LIBRARIES
            "requests>=2.0.0",
            "biopython>=1.83",
            "pubchempy>=1.0.4",
        ],
        # NOTE: NO extra_packages. We rely entirely on the code above.
    )
    print(f"✅ Created remote agent: {remote_agent.resource_name}")

def main(_):
    load_dotenv()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    
    if not bucket:
         # Fallback if env var is missing
        bucket = "rsabawi-staging-gs" 
        
    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")

    if FLAGS.create:
        create_agent()

if __name__ == "__main__":
    app.run(main)