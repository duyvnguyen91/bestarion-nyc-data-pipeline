# Same Agents for Learning 

## How to run
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install google-adk google-genai

gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="civil-treat-482015-n6"                                                                                                      took 4s  agents
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI="true"
python3 basic_agent.py
```