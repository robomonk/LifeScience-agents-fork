import google.adk.code_executors
import pkgutil

print("--- Available Classes in google.adk.code_executors ---")
print(dir(google.adk.code_executors))

print("\n--- Submodules in google.adk.code_executors ---")
package = google.adk.code_executors
for _, name, _ in pkgutil.iter_modules(package.__path__):
    print(f" - {name}")