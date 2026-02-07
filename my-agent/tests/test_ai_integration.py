"""
Integration tests for AI configuration with Groq API.

These tests verify that the AI configuration works end-to-end with AgentField.
Requires: GROQ_API_KEY set in .env, network access to Groq API.

Run with: pytest tests/test_ai_integration.py -v
Skip if no API key: pytest tests/test_ai_integration.py -v -k "not integration"
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
agent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(agent_dir))

from dotenv import load_dotenv
load_dotenv(agent_dir / ".env")


# Skip all tests in this module if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set - skipping integration tests"
)


class TestGroqAPIIntegration:
    """Integration tests for Groq API connectivity (basic checks only)."""

    def test_groq_api_key_valid_format(self):
        """Test that Groq API key has valid format."""
        api_key = os.getenv("GROQ_API_KEY")
        assert api_key is not None
        assert api_key.startswith("gsk_"), "Groq API keys should start with 'gsk_'"
        assert len(api_key) > 20, "API key seems too short"

    @pytest.mark.integration
    def test_groq_api_connection(self):
        """Test that Groq API is reachable."""
        from groq import Groq
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Just test we can connect and get a response object
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )
        
        # API is reachable if we get a completion object
        assert completion is not None
        assert completion.id is not None, "API should return a completion ID"
        print(f"✅ Groq API connection successful (completion id: {completion.id})")


class TestAgentFieldAIConfig:
    """Test AgentField AI configuration."""

    def test_agent_ai_config_model(self):
        """Test that agent AI config has correct model."""
        from main import app
        
        assert app.ai_config is not None
        assert "gpt-oss-120b" in app.ai_config.model.lower()

    def test_agent_ai_config_has_api_key(self):
        """Test that agent AI config has API key set."""
        from main import app
        
        assert app.ai_config is not None
        assert app.ai_config.api_key is not None
        assert len(app.ai_config.api_key) > 0


class TestAgentFieldAIFunction:
    """Test AgentField's built-in AI function with the configured model."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agentfield_ai_simple(self):
        """Test AgentField's ai() function with a simple prompt."""
        from main import app
        
        result = await app.ai(
            system="You are a helpful assistant.",
            user="Say HELLO in one word.",
        )
        
        print(f"AgentField AI response: '{result}'")
        assert result is not None, "AI should return a response"
        assert len(str(result).strip()) > 0, f"Response should not be empty, got: '{result}'"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agentfield_ai_clinical_decision(self):
        """Test AgentField's ai() function with clinical prompt."""
        from main import app
        from pydantic import BaseModel, Field
        
        class ClinicalDecision(BaseModel):
            decision: str = Field(description="ESCALATE or MONITOR")
            confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
            reasoning: str = Field(description="Brief reasoning")
        
        clinical_prompt = """
Patient data:
- Age: 68
- Conditions: hypertension, diabetes
- CRP: 12.5 mg/L (elevated, normal < 10)
- Heart rate trend: increasing over 24h

Should this patient be escalated for clinical review? Respond with decision, confidence, and brief reasoning.
"""
        
        result = await app.ai(
            system="You are a clinical decision support system. Assess patient risk.",
            user=clinical_prompt,
            schema=ClinicalDecision,
        )
        
        print(f"AgentField clinical decision: {result}")
        assert result is not None, "AI should return a structured response"
        assert hasattr(result, 'decision'), "Response should have 'decision' field"
        assert result.decision.upper() in ["ESCALATE", "MONITOR"], f"Invalid decision: {result.decision}"
        assert 0 <= result.confidence <= 1, f"Confidence out of range: {result.confidence}"
        print(f"✅ Clinical decision: {result.decision} (confidence: {result.confidence})")
