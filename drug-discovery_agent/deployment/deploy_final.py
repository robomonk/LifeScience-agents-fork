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
from typing import Any

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP storage bucket for staging.")
flags.DEFINE_bool("create", False, "Creates a new agent.")
flags.DEFINE_bool("list", False, "Lists all agents.")

class DrugDiscoveryFinalEngine:
    def __init__(self):
        print("Final Engine Initialized")

    def _search_pubchem(self, query):
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

    def _search_pubmed_rest(self, query):
        """Tool: Search PubMed using standard HTTP requests."""
        import requests
        import xml.etree.ElementTree as ET
        
        try:
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax=3&usehistory=y"
            
            r = requests.get(search_url)
            if r.status_code != 200:
                return f"PubMed API Error: {r.status_code}"
            
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

    # --- THE FIX: BULLETPROOF INPUT HANDLING ---
    def query(self, input: Any, **kwargs) -> str:
        """
        Main Agent Logic.
        Accepts 'Any' type to prevent crashes if Gemini sends a Dict/List.
        """
        # 1. ROBUST CONVERSION: Ensure we have a string, no matter what Gemini sends.
        if isinstance(input, dict):
            # If Gemini sends {'input': '...'}, extract it
            query_text = input.get("input", str(input))
        elif isinstance(input, list):
            # If Gemini sends chat history, take the last message
            query_text = str(input[-1]) if input else ""
        else:
            query_text = str(input)

        # 2. LOGIC (Safe to run .lower() now)
        input_lower = query_text.lower()
        response = []
        
        response.append(f"🤖 Processing Query: '{query_text}'")

        if "pubchem" in input_lower or "structure" in input_lower or "weight" in input_lower or "formula" in input_lower:
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

    print(f"🚀 Deploying ROBUST AGENT: {AGENT_NAME}...")
    
    remote_agent = agent_engines.create(
        DrugDiscoveryFinalEngine(),
        display_name=AGENT_NAME,
        requirements=[
            # DOWNGRADE to known stable version
            "google-cloud-aiplatform==1.126.1",  # Downgrade from 1.131.0
            "pydantic==2.11.7",
            "cloudpickle==3.1.1",
            "pubchempy>=1.0.4",
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