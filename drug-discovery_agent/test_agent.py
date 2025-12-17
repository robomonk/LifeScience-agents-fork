import os
import argparse
from dotenv import load_dotenv
import vertexai
from vertexai import agent_engines

def test_agent(resource_id, query):
    # 1. Load Environment & Initialize
    load_dotenv()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    
    print(f"🔌 Connecting to Vertex AI (Project: {project_id})...")
    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")

    # 2. Connect to the Remote Agent
    print(f"🔗 Retrieving Agent: {resource_id}...")
    try:
        agent = agent_engines.get(resource_id)
    except Exception as e:
        print(f"❌ Failed to find agent. Check Resource ID.\nError: {e}")
        return

    # 3. Send Query
    print(f"📤 Sending Query: '{query}'")
    print("-" * 40)
    
    try:
        # We use query() because your deployed class defines query()
        response = agent.query(input=query)
        print("✅ RESPONSE RECEIVED:")
        print(response)
    except Exception as e:
        print(f"❌ Query Failed:\n{e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("resource_id", help="The full Resource ID (projects/...) of the agent")
    parser.add_argument("--query", default="Search pubmed for cancer", help="The question to ask")
    args = parser.parse_args()

    test_agent(args.resource_id, args.query)