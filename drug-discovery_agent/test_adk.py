import sys
import os
from dotenv import load_dotenv
import vertexai
from vertexai.preview import reasoning_engines

def main():
    load_dotenv()
    
    # 1. Parse Arguments
    if len(sys.argv) < 3:
        print("Usage: python test_adk.py <RESOURCE_ID> <QUERY>")
        print('Example: python test_adk.py projects/.../reasoningEngines/123 "What is aspirin?"')
        sys.exit(1)

    resource_id = sys.argv[1]
    query_text = sys.argv[2]
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    print(f"🔌 Connecting to Vertex AI (Project: {project_id})...")
    vertexai.init(project=project_id, location=location)

    try:
        # 2. Retrieve the Agent using the STANDARD client
        print(f"🔗 Retrieving Agent: {resource_id}...")
        remote_agent = reasoning_engines.ReasoningEngine(resource_id)
        
        # 3. Send Query
        print(f"📤 Sending Query: '{query_text}'")
        print("-" * 40)
        
        # Note: AdkApp agents usually expect 'input' or 'prompt'
        # We pass it as a keyword argument to be safe.
        response = remote_agent.query(input=query_text)
        
        print("✅ RESPONSE RECEIVED:")
        print(response)
        print("-" * 40)

    except Exception as e:
        print(f"\n❌ Query Failed:\n{str(e)}")

if __name__ == "__main__":
    main()