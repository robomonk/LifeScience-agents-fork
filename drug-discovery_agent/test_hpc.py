import sys
import vertexai
from vertexai.preview import reasoning_engines

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_hpc.py <AGENT_RESOURCE_ID>")
        sys.exit(1)

    agent_id = sys.argv[1]
    
    # Connect
    remote_agent = reasoning_engines.ReasoningEngine(agent_id)
    print(f"🔌 Connecting to Agent: {agent_id}")
    
    # 1. Create Session
    print("⏳ Creating Session...")
    session_data = remote_agent.create_session(user_id="test-user-01")
    print(f"✅ Session Created: {session_data}")
    
    # 2. Extract Session ID (CORRECTED KEY IS 'id')
    session_id = session_data['id']

    # 3. Query the Agent using the ID
    query = (
        "I need to run a large molecular dynamics simulation for a new candidate. "
        "Please deploy a high-performance cluster with 8 nodes optimized for compute, "
        "and then submit the job 'simulation_v1.sh'."
    )
    
    print(f"\n📤 Query: {query}")
    print("🤖 Agent is thinking (Deploying Infrastructure)...")
    
    try:
        # Pass session_id to maintain state
        response = remote_agent.query(session_id=session_id, input=query)
        print("\n✅ Response:")
        print(response)
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()