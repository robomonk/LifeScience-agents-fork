import sys
import vertexai
from vertexai.preview import reasoning_engines

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_session.py <RESOURCE_ID> <QUERY>")
        sys.exit(1)

    resource_id = sys.argv[1]
    query = sys.argv[2]

    # 1. Connect
    remote_agent = reasoning_engines.ReasoningEngine(resource_id)

    # 2. Create Session (Standard ADK Pattern)
    print("⏳ Creating Session...")
    session = remote_agent.create_session()
    print(f"✅ Session Created: {session.resource_name}")

    # 3. Query the Session
    print(f"📤 Sending Query: {query}")
    response = session.query(query)

    print("✅ Response:")
    print(response)

if __name__ == "__main__":
    main()