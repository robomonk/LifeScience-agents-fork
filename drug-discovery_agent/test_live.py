# test_live.py
import sys
from vertexai.preview import reasoning_engines

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_live.py <RESOURCE_ID> <QUERY>")
        return

    resource_id = sys.argv[1]
    user_query = sys.argv[2]

    print(f"🔌 Connecting to Agent: {resource_id}")
    
    try:
        # Load the remote agent
        remote_agent = reasoning_engines.ReasoningEngine(resource_id)
        
        print(f"📤 Sending Query: {user_query}")
        print("🤖 Agent is thinking...")
        
        # Execute
        response = remote_agent.query(input=user_query)
        
        print("\n✅ Response:")
        print(response)
        
    except Exception as e:
        print(f"\n❌ Error:\n{e}")

if __name__ == "__main__":
    main()