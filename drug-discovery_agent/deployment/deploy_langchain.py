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
from vertexai.preview import reasoning_engines
from langchain_core.tools import tool

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP storage bucket for staging.")
flags.DEFINE_bool("create", False, "Creates a new agent.")

# --- 1. DEFINE TOOLS (Standard LangChain Decorator) ---

@tool
def search_pubchem(query: str) -> str:
    """
    Search PubChem for a compound's structure, CID, formula, and molecular weight.
    Use this when the user asks for chemical structures, formulas, or properties.
    Args:
        query: The name of the chemical compound (e.g., 'aspirin').
    """
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

@tool
def search_pubmed(query: str) -> str:
    """
    Search PubMed for scientific papers and literature.
    Use this when the user asks for research papers, studies, or medical abstracts.
    Args:
        query: The search terms (e.g., 'lung cancer treatment').
    """
    import requests
    import xml.etree.ElementTree as ET
    try:
        # 1. ESearch
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax=3&usehistory=y"
        r = requests.get(search_url)
        root = ET.fromstring(r.text)
        id_list = [id_elem.text for id_elem in root.findall(".//Id")]
        
        if not id_list:
            return "No articles found."

        # 2. EFetch
        ids = ",".join(id_list)
        fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={ids}&retmode=text&rettype=abstract"
        r_fetch = requests.get(fetch_url)
        return f"PubMed Results:\n{r_fetch.text[:1000]}..." 
    except Exception as e:
        return f"PubMed Error: {str(e)}"

# --- 2. DEPLOYMENT CONFIG ---

def create_agent():
    AGENT_NAME = "drug-discovery-lc"
    
    print(f"🚀 Deploying LANGCHAIN AGENT: {AGENT_NAME}...")
    
    # We use the OFFICIAL LangChainAgent class from Vertex AI.
    # This automatically handles input schemas, history, and serialization.
    remote_agent = reasoning_engines.LangchainAgent(
        model="gemini-1.5-flash-001",  # Use a standard stable model
        tools=[search_pubchem, search_pubmed],
        agent_executor_kwargs={"return_intermediate_steps": True},
    )
    
    # The SDK handles the packaging for us
    remote_agent.set_up()
    
    # Actual Deployment
    # We explicitly pin versions to ensure stability
    deployed_agent = reasoning_engines.ReasoningEngine.create(
        remote_agent,
        display_name=AGENT_NAME,
        requirements=[
            "google-cloud-aiplatform==1.126.1", # STABLE VERSION
            "pydantic==2.11.7",
            "cloudpickle==3.1.1",
            "pubchempy>=1.0.4",
            "requests>=2.0.0",
            "langchain>=0.1.0",
            "langchain-google-vertexai",
            "langchain-core"
        ],
    )
    print(f"✅ Created standard LangChain agent: {deployed_agent.resource_name}")

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