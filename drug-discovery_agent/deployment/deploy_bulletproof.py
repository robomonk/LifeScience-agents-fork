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

# --- THE BULLETPROOF ENGINE ---
class BulletproofEngine:
    def __init__(self):
        print("Bulletproof Engine Initialized")

    # 1. PERMISSIVE SIGNATURE: Accepts 'input', 'prompt', or anything else in **kwargs
    def query(self, input: Any = None, prompt: Any = None, **kwargs) -> str:
        """
        Debug Probe: Returns exactly what arguments Gemini sent.
        """
        # Figure out what the primary input really is
        actual_input = input or prompt or kwargs.get('message') or "NO_INPUT_FOUND"
        
        # Construct a debug report
        report = (
            f"✅ DEBUG PROBE SUCCESS.\n"
            f"--------------------------------------------------\n"
            f"1. Primary Input Value: '{actual_input}'\n"
            f"2. Primary Input Type:  {type(actual_input)}\n"
            f"3. Full kwargs received: {kwargs}\n"
            f"--------------------------------------------------"
        )
        return report

def create_agent():
    AGENT_NAME = "agentic-tx"
    
    # Cleanup old agents to avoid confusion
    try:
        agents = agent_engines.list()
        for agent in agents:
            if agent.display_name == AGENT_NAME:
                print(f"Deleting old agent: {agent.resource_name}")
                agent.delete(force=True)
    except:
        pass

    print(f"🚀 Deploying BULLETPROOF AGENT: {AGENT_NAME}...")
    
    remote_agent = agent_engines.create(
        BulletproofEngine(),
        display_name=AGENT_NAME,
        requirements=[
            # SYSTEM (Proven Stable)
            "google-cloud-aiplatform==1.131.0",
            "pydantic==2.11.7",
            "cloudpickle==3.1.1",
        ],
    )
    print(f"✅ Created remote agent: {remote_agent.resource_name}")

def main(_):
    load_dotenv()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    
    if not bucket:
        bucket = "rsabawi-staging-gs" # Fallback
        
    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")

    if FLAGS.create:
        create_agent()

if __name__ == "__main__":
    app.run(main)