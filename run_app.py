import os
import sys
import subprocess

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY environment variable is not set.")
    print("Set it with: $env:GROQ_API_KEY='your-key-here'")
    exit(1)
os.environ["GROQ_API_KEY"] = api_key
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
