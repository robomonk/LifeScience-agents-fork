import sys
import json
from google.cloud import aiplatform_v1beta1
from google.protobuf import struct_pb2

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_hpc_manual.py <AGENT_RESOURCE_ID>")
        sys.exit(1)

    # Parse the Resource ID (projects/.../locations/.../reasoningEngines/...)
    resource_name = sys.argv[1]
    
    # 1. Initialize the Low-Level Client
    client_options = {"api_endpoint": "us-central1-aiplatform.googleapis.com"}
    client = aiplatform_v1beta1.ReasoningEngineExecutionServiceClient(client_options=client_options)

    print(f"🔌 Connecting to Agent via Low-Level API: {resource_name}")

    # 2. Query Payload
    # We combine the session creation and query logic if possible, 
    # but for ADK we usually need a session first. 
    # Since the high-level client failed, we will try a direct stateless query 
    # or just assume a new session is created if we don't pass one.
    
    user_query = (
        "Check online for the current spot price of a c2-standard-60 VM in us-central1. If it is below $3/hour, list my active VMs to check if I have room for a new cluster."
    )

    # Construct the JSON input arguments
    # ADK expects: {"input": "...", "session_id": "...", "user_id": "..."}
    input_struct = struct_pb2.Struct()
    input_struct.update({
        "input": user_query,
        "user_id": "test-user-01" 
        # Note: If we don't pass a session_id, ADK usually creates a new one 
        # for this turn. For testing this is fine.
    })

    request = aiplatform_v1beta1.QueryReasoningEngineRequest(
        name=resource_name,
        input=input_struct
    )

    print(f"\n📤 Sending Query: {user_query}")
    print("🤖 Agent is thinking (this ignores local client errors)...")

    try:
        response = client.query_reasoning_engine(request=request)
        
        # Parse output
        output_json = response.output
        # The response is usually a Struct, we convert to dict for printing
        print("\n✅ Raw Response:")
        print(output_json)
        
        # Try to print just the text if available
        if "output" in output_json:
            print(f"\n📝 Answer: {output_json['output']}")
            
    except Exception as e:
        print(f"\n❌ API Error: {e}")

if __name__ == "__main__":
    main()