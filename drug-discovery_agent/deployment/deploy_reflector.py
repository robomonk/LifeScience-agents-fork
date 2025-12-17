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

# --- THE REFLECTOR ENGINE ---
class ReflectorEngine:
    def __init__(self):
        print("Reflector Initialized")

    # PERMISSIVE QUERY: Accepts ANYTHING
    def query(self, **kwargs) -> str:
        """
        Reflects all arguments back to the user.
        """
        return f"✅ QUERY METHOD TRIGGERED.\n\nI received these inputs:\n{kwargs}"

    # PERMISSIVE STREAM: Accepts ANYTHING
    def stream_query(self, **kwargs):
        """
        Reflects all arguments back as a stream.
        """
        yield f"✅ STREAM_QUERY METHOD TRIGGERED.\n"
        yield f"I received these inputs:\n{kwargs}"

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
    print(f"🚀 Deploying REFLECTOR AGENT: {AGENT_NAME}...")
    
    remote_agent = agent_engines.create(
        ReflectorEngine(),
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
    
    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")

    if FLAGS.create:
        create_agent()

if __name__ == "__main__":
    app.run(main)