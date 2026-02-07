"""
Unit tests for main.py configuration

Tests validate:
1. Environment variables are loaded
2. Agent configuration is correct
3. AI config uses Groq
"""

import pytest
import os
from pathlib import Path


class TestMainConfiguration:
    """Tests for main.py agent configuration."""

    def test_env_file_exists(self):
        """Test that .env file exists."""
        env_path = Path(__file__).parent.parent / ".env"
        assert env_path.exists(), ".env file not found"

    def test_groq_api_key_set(self):
        """Test that GROQ_API_KEY is set in .env."""
        from dotenv import load_dotenv
        
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
        
        api_key = os.getenv("GROQ_API_KEY")
        assert api_key is not None, "GROQ_API_KEY not set in .env"
        assert api_key.startswith("gsk_"), "GROQ_API_KEY should start with 'gsk_'"

    def test_main_imports(self):
        """Test that main.py can be imported without errors."""
        # Change to my-agent directory for relative imports
        import sys
        agent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(agent_dir))
        
        # This will fail if there are import errors
        try:
            from main import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import main.py: {e}")

    def test_agent_node_id(self):
        """Test that agent has correct node_id."""
        import sys
        agent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(agent_dir))
        
        from main import app
        assert app.node_id == "clinical-triage"

    def test_agent_has_ai_config(self):
        """Test that agent has AI configuration."""
        import sys
        agent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(agent_dir))
        
        from main import app
        assert app.ai_config is not None, "AI config not set"

    def test_ai_config_uses_groq(self):
        """Test that AI config uses Groq model."""
        import sys
        agent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(agent_dir))
        
        from main import app
        # Check that the model string contains 'groq' and 'gpt-oss-120b'
        model = app.ai_config.model.lower()
        assert "groq" in model, "AI config should use Groq"
        assert "gpt-oss-120b" in model, "AI config should use GPT-OSS-120B model"

    def test_ai_config_temperature(self):
        """Test that AI config has appropriate temperature for clinical reasoning."""
        import sys
        agent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(agent_dir))
        
        from main import app
        # Lower temperature for more deterministic clinical reasoning
        assert app.ai_config.temperature <= 0.5, "Temperature should be low for clinical reasoning"
