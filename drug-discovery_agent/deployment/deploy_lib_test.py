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
import traceback

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP storage bucket for staging.")
flags.DEFINE_bool("create", False, "Creates a new agent.")
flags.DEFINE_bool("list", False, "Lists all agents.")

class LibraryTestEngine:
    def __init__(self):
        print("Library Test Engine Initialized")

    def query(self, input: str) -> str:
        """
        Diagnostic Router: Tests imports one by one.
        """
        cmd = input.lower().strip()

        if "requests" in cmd:
            try:
                import requests
                return f"✅ Requests Imported! Version: {requests.__version__}"
            except Exception as e:
                return f"❌ Requests Failed: {e}"

        if "pubchem" in cmd:
            try:
                import pubchempy
                return f"✅ PubChemPy Imported! (No version attr)"
            except Exception as e:
                return f"❌ PubChemPy Failed: {e}"

        if "bio" in cmd:
            try:
                import Bio
                from Bio import Entrez
                return f"✅ Biopython Imported! Version: {Bio.__version__}"
            except Exception as e:
                return f"❌ Biopython Failed: {e}"

        if "search" in cmd:
            try:
                from googlesearch import search
                return f"✅ Google Search Imported!"
            except Exception as e:
                return f"❌ Google Search Failed: {e}"

        return "Ready to test. Type: 'requests', 'pubchem', 'bio', or 'search'."

def create_agent():
    AGENT_NAME = "agentic-tx"
    
    # Cleanup
    try:
        agents = agent_engines.list()
        for agent in agents:
            if agent.display_name == AGENT_NAME:
                print(f"Deleting old agent: {agent.resource_name}")
                agent.delete(force=True)
    except:
        pass

    print(f"🚀 Deploying LIBRARY TESTER: {AGENT_NAME}...")
    
    remote_agent = agent_engines.create(
        LibraryTestEngine(),
        display_name=AGENT_NAME,
        requirements=[
            # SYSTEM (Pinned & Proven)
            "google-cloud-aiplatform==1.131.0",
            "pydantic==2.11.7",
            "cloudpickle==3.1.1",
            
            # CANDIDATES FOR CRASHING
            "requests>=2.0.0",
            "biopython>=1.83",
            "pubchempy>=1.0.4",
            "google-search-results>=2.4.2"
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