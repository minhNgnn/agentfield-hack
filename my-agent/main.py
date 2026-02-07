import os
from dotenv import load_dotenv
from agentfield import Agent, AIConfig
from reasoners import reasoners_router

# Load environment variables from .env file
load_dotenv()

# Clinical Triage Agent - AI-powered clinical decision support
app = Agent(
    node_id="clinical-triage",
    agentfield_server="http://localhost:8080",
    version="1.0.0",
    dev_mode=True,

    # AI configuration using Groq API with GPT-OSS-120B
    ai_config=AIConfig(
        model="groq/openai/gpt-oss-120b",  # Groq's GPT-OSS-120B model
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,  # Lower for more deterministic clinical reasoning
        max_tokens=4096,
    ),
)

# Include reasoners from separate file
app.include_router(reasoners_router)

if __name__ == "__main__":
    # Auto-discover available port starting from 8000
    app.serve(auto_port=True, dev=True, reload=False)
