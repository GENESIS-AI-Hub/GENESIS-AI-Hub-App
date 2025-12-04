from google.adk.tools import google_search
import inspect

print(f"Type of google_search: {type(google_search)}")
print(f"Dir of google_search: {dir(google_search)}")
try:
    print(f"Source of google_search: {inspect.getsource(google_search)}")
except:
    print("Cannot get source.")
