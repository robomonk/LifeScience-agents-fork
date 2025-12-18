from google.adk.agents import LlmAgent
from google.adk.code_executors import UnsafeLocalCodeExecutor

# Initialize a dummy agent
agent = LlmAgent(
    name="inspector",
    model="gemini-2.0-flash",
    instruction="test",
    code_executor=UnsafeLocalCodeExecutor()
)

# PRINT THE TRUTH
print("\n🔎 INSPECTING AGENT METHODS:")
methods = [method for method in dir(agent) if not method.startswith('_')]
print(methods)

print("\n--------------------------------")
if 'query' in methods: print("✅ .query() exists")
elif 'run' in methods: print("✅ .run() exists")
elif 'invoke' in methods: print("✅ .invoke() exists")
else: print("❌ No standard method found. Check the list above.")