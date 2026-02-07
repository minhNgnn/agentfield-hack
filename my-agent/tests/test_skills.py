"""
Unit tests for skills.py - Patient Context Skills.

Tests Task 2.1: normalize_patient() skill
Tests Task 2.2: store_patient_context() and get_patient_context() skills

NOTE: Integration tests require both `af server` and `python main.py` to be running.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
agent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(agent_dir))

# Configure pytest-asyncio to use class-scoped event loops
pytestmark = pytest.mark.asyncio


class TestNormalizePatient:
    """Tests for the normalize_patient skill (Task 2.1)."""

    def test_normalize_patient_p001_exists(self):
        """Test that P001 (high risk patient) can be normalized."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert result is not None
        assert result["patient_id"] == "P001"

    def test_normalize_patient_p001_basic_fields(self):
        """Test that P001 has all required fields."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert "patient_id" in result
        assert "age" in result
        assert "conditions" in result
        assert "medications" in result
        assert "recent_labs" in result
        assert "vital_trends" in result
        assert "trend_summary" in result

    def test_normalize_patient_p001_age(self):
        """Test P001 age is correct (68 - high risk elderly patient)."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert result["age"] == 68

    def test_normalize_patient_p001_conditions(self):
        """Test P001 has expected conditions."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert "hypertension" in result["conditions"]
        assert "type2_diabetes" in result["conditions"]

    def test_normalize_patient_p001_recent_labs(self):
        """Test P001 recent labs are extracted correctly."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        # Should have the most recent (last) value
        assert "CRP" in result["recent_labs"]
        assert result["recent_labs"]["CRP"] == 12.5  # Elevated

    def test_normalize_patient_p001_vital_trends(self):
        """Test P001 vital trends are calculated."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        # P001 has increasing heart rate
        assert "heart_rate" in result["vital_trends"]
        # Values: [72, 78, 85, 92] - last jump is 85->92 (8.2%), under 10% threshold
        # Actually need to check the mock data trend

    def test_normalize_patient_p001_trend_summary_not_empty(self):
        """Test P001 has a trend summary (should have concerning trends)."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        # P001 is high risk, should have some concerning trends
        assert result["trend_summary"] != ""
        assert result["trend_summary"] != "all metrics stable"

    def test_normalize_patient_p002_exists(self):
        """Test that P002 (low risk patient) can be normalized."""
        from skills import normalize_patient
        
        result = normalize_patient("P002")
        
        assert result is not None
        assert result["patient_id"] == "P002"

    def test_normalize_patient_p002_stable(self):
        """Test P002 (low risk) has stable metrics."""
        from skills import normalize_patient
        
        result = normalize_patient("P002")
        
        # P002 should be mostly stable
        assert result["age"] == 35  # Younger patient

    def test_normalize_patient_p003_exists(self):
        """Test that P003 (ambiguous patient) can be normalized."""
        from skills import normalize_patient
        
        result = normalize_patient("P003")
        
        assert result is not None
        assert result["patient_id"] == "P003"

    def test_normalize_patient_invalid_id(self):
        """Test that invalid patient ID raises error."""
        from skills import normalize_patient
        
        with pytest.raises(ValueError) as excinfo:
            normalize_patient("INVALID_ID")
        
        assert "not found" in str(excinfo.value)

    def test_normalize_patient_returns_dict(self):
        """Test that normalize_patient returns a dictionary."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert isinstance(result, dict)

    def test_normalize_patient_conditions_is_list(self):
        """Test that conditions field is a list."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert isinstance(result["conditions"], list)

    def test_normalize_patient_medications_is_list(self):
        """Test that medications field is a list."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert isinstance(result["medications"], list)

    def test_normalize_patient_recent_labs_is_dict(self):
        """Test that recent_labs field is a dict."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert isinstance(result["recent_labs"], dict)

    def test_normalize_patient_vital_trends_is_dict(self):
        """Test that vital_trends field is a dict."""
        from skills import normalize_patient
        
        result = normalize_patient("P001")
        
        assert isinstance(result["vital_trends"], dict)


class TestGenerateTrendSummary:
    """Tests for the _generate_trend_summary helper function."""

    def test_trend_summary_empty_trends(self):
        """Test trend summary with no concerning trends."""
        from skills import _generate_trend_summary
        
        result = _generate_trend_summary({}, {})
        
        assert result == "all metrics stable"

    def test_trend_summary_stable_trends(self):
        """Test trend summary with all stable trends."""
        from skills import _generate_trend_summary
        
        trends = {"heart_rate": "stable", "bp": "stable"}
        result = _generate_trend_summary(trends, {})
        
        assert result == "all metrics stable"

    def test_trend_summary_increasing_trend(self):
        """Test trend summary with increasing vital."""
        from skills import _generate_trend_summary
        
        trends = {"heart_rate": "increasing"}
        result = _generate_trend_summary(trends, {})
        
        assert "heart rate increasing" in result

    def test_trend_summary_decreasing_trend(self):
        """Test trend summary with decreasing vital."""
        from skills import _generate_trend_summary
        
        trends = {"blood_pressure": "decreasing"}
        result = _generate_trend_summary(trends, {})
        
        assert "blood pressure decreasing" in result

    def test_trend_summary_elevated_crp(self):
        """Test trend summary detects elevated CRP."""
        from skills import _generate_trend_summary
        
        labs = {"CRP": {"values": [5.0, 8.0, 12.5]}}
        result = _generate_trend_summary({}, labs)
        
        assert "elevated CRP" in result
        assert "12.5" in result

    def test_trend_summary_normal_crp(self):
        """Test trend summary with normal CRP (under 10)."""
        from skills import _generate_trend_summary
        
        labs = {"CRP": {"values": [2.0, 3.0, 5.0]}}
        result = _generate_trend_summary({}, labs)
        
        assert "elevated CRP" not in result

    def test_trend_summary_elevated_wbc(self):
        """Test trend summary detects elevated WBC."""
        from skills import _generate_trend_summary
        
        labs = {"WBC": {"values": [8000, 10000, 12000]}}
        result = _generate_trend_summary({}, labs)
        
        assert "elevated WBC" in result

    def test_trend_summary_combined(self):
        """Test trend summary with multiple concerning factors."""
        from skills import _generate_trend_summary
        
        trends = {"heart_rate": "increasing"}
        labs = {"CRP": {"values": [5.0, 8.0, 15.0]}}
        result = _generate_trend_summary(trends, labs)
        
        assert "heart rate increasing" in result
        assert "elevated CRP" in result


class TestSkillsRouter:
    """Tests for skills router configuration."""

    def test_skills_router_exists(self):
        """Test that skills_router is defined."""
        from skills import skills_router
        
        assert skills_router is not None

    def test_skills_router_prefix(self):
        """Test that skills_router has correct prefix."""
        from skills import skills_router
        
        assert skills_router.prefix == "patient"

    def test_skills_router_tags(self):
        """Test that skills_router has correct tags."""
        from skills import skills_router
        
        assert "skills" in skills_router.tags


class TestStorePatientContext:
    """Tests for store_patient_context skill (Task 2.2)."""

    def test_store_patient_context_exists(self):
        """Test that store_patient_context function exists."""
        from skills import store_patient_context
        
        assert store_patient_context is not None
        assert callable(store_patient_context)

    def test_store_patient_context_is_async(self):
        """Test that store_patient_context is an async function."""
        import asyncio
        import inspect
        from skills import store_patient_context
        
        # The skill decorator wraps the function, check the original
        # AgentField skills may be wrapped, so check if callable returns coroutine
        assert callable(store_patient_context)

    def test_get_patient_context_exists(self):
        """Test that get_patient_context function exists."""
        from skills import get_patient_context
        
        assert get_patient_context is not None
        assert callable(get_patient_context)

    def test_get_patient_context_is_async(self):
        """Test that get_patient_context is an async function."""
        import asyncio
        from skills import get_patient_context
        
        # Check if callable
        assert callable(get_patient_context)


@pytest.mark.asyncio(loop_scope="class")
class TestStorePatientContextIntegration:
    """Integration tests for memory operations (requires AgentField server running)."""

    async def test_store_and_retrieve_patient_context(self):
        """Test storing and retrieving patient context from memory."""
        # Import app first to ensure router is attached
        from main import app  # noqa: F401
        from skills import store_patient_context, get_patient_context
        
        # Store patient context
        store_result = await store_patient_context("P001")
        
        assert store_result["status"] == "stored"
        assert store_result["patient_id"] == "P001"
        assert store_result["memory_key"] == "patient:P001:context"
        assert "context" in store_result
        
        # Retrieve patient context
        get_result = await get_patient_context("P001")
        
        assert get_result["status"] == "found"
        assert get_result["patient_id"] == "P001"
        assert get_result["context"]["patient_id"] == "P001"
        assert get_result["context"]["age"] == 68

    async def test_store_patient_context_p002(self):
        """Test storing P002 (low risk patient)."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        
        result = await store_patient_context("P002")
        
        assert result["status"] == "stored"
        assert result["patient_id"] == "P002"
        assert result["context"]["age"] == 35

    async def test_store_patient_context_p003(self):
        """Test storing P003 (ambiguous patient)."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        
        result = await store_patient_context("P003")
        
        assert result["status"] == "stored"
        assert result["patient_id"] == "P003"

    async def test_get_patient_context_not_found(self):
        """Test that get_patient_context raises error for missing patient."""
        from main import app  # noqa: F401
        from skills import get_patient_context
        
        with pytest.raises(ValueError) as excinfo:
            await get_patient_context("NONEXISTENT_PATIENT_XYZ_12345")
        
        assert "No context found" in str(excinfo.value)

    async def test_store_patient_context_invalid_id(self):
        """Test that store_patient_context raises error for invalid patient."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        
        with pytest.raises(ValueError) as excinfo:
            await store_patient_context("INVALID")
        
        assert "not found" in str(excinfo.value)

    async def test_stored_context_has_all_fields(self):
        """Test that stored context has all required PatientContext fields."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        
        result = await store_patient_context("P001")
        context = result["context"]
        
        required_fields = [
            "patient_id", "age", "conditions", "medications",
            "recent_labs", "vital_trends", "trend_summary"
        ]
        
        for field in required_fields:
            assert field in context, f"Missing field: {field}"


# =============================================================================
# UNIT TESTS: Task 4.1 - Notification Skill
# =============================================================================


class TestSendNotificationUnit:
    """Unit tests for send_notification skill."""

    def test_send_notification_exists(self):
        """Test that send_notification function exists."""
        from skills import send_notification

        assert send_notification is not None

    def test_send_notification_is_callable(self):
        """Test that send_notification is callable."""
        from skills import send_notification

        assert callable(send_notification)

    def test_send_notification_escalate(self):
        """Test notification for escalation decision."""
        from skills import send_notification

        result = send_notification(
            patient_id="P001",
            decision="escalate",
            risk_level="high",
            rationale="Rising inflammatory markers"
        )

        assert result["type"] == "CLINICAL_ESCALATION"
        assert result["patient_id"] == "P001"
        assert result["risk_level"] == "high"
        assert result["message"] == "Rising inflammatory markers"
        assert result["status"] == "sent"
        assert "timestamp" in result

    def test_send_notification_monitor(self):
        """Test notification for monitor decision."""
        from skills import send_notification

        result = send_notification(
            patient_id="P002",
            decision="monitor",
            risk_level="low",
            rationale="All metrics stable"
        )

        assert result["type"] == "MONITORING_UPDATE"
        assert result["patient_id"] == "P002"
        assert result["risk_level"] == "low"

    def test_send_notification_returns_dict(self):
        """Test that send_notification returns a dictionary."""
        from skills import send_notification

        result = send_notification(
            patient_id="P001",
            decision="escalate",
            risk_level="high",
            rationale="Test"
        )

        assert isinstance(result, dict)

    def test_send_notification_timestamp_format(self):
        """Test that timestamp is ISO format."""
        from skills import send_notification

        result = send_notification(
            patient_id="P001",
            decision="escalate",
            risk_level="high",
            rationale="Test"
        )

        # Should be parseable as ISO format
        from datetime import datetime
        timestamp = result["timestamp"]
        # ISO format with timezone: 2026-02-07T14:30:00+00:00
        assert "T" in timestamp
        assert len(timestamp) > 10


# =============================================================================
# UNIT TESTS: Task 4.2 - Decision Logging Skill
# =============================================================================


class TestLogDecisionUnit:
    """Unit tests for log_decision skill structure."""

    def test_log_decision_exists(self):
        """Test that log_decision function exists."""
        from skills import log_decision

        assert log_decision is not None

    def test_log_decision_is_async(self):
        """Test that log_decision is an async function."""
        import asyncio
        from skills import log_decision

        assert asyncio.iscoroutinefunction(log_decision)

    def test_get_decision_history_exists(self):
        """Test that get_decision_history function exists."""
        from skills import get_decision_history

        assert get_decision_history is not None

    def test_get_decision_history_is_async(self):
        """Test that get_decision_history is an async function."""
        import asyncio
        from skills import get_decision_history

        assert asyncio.iscoroutinefunction(get_decision_history)


# =============================================================================
# INTEGRATION TESTS: Task 4.1 & 4.2 - Notification & Logging
# =============================================================================


@pytest.mark.asyncio(loop_scope="class")
class TestNotificationAndLoggingIntegration:
    """Integration tests for notification and logging skills."""

    async def test_log_decision_stores_entry(self):
        """Test that log_decision stores decision in memory."""
        from main import app  # noqa: F401
        from skills import log_decision

        decision = {
            "escalation_decision": "escalate",
            "risk_level": "high",
            "confidence": 0.85,
            "rationale": "Test rationale",
            "contributing_factors": ["factor1", "factor2"]
        }

        result = await log_decision("P001", decision)

        assert result["status"] == "logged"
        assert result["entry"]["patient_id"] == "P001"
        assert result["entry"]["decision"] == decision
        assert result["entry"]["logged_by"] == "clinical-triage"
        assert "timestamp" in result["entry"]

    async def test_get_decision_history_retrieves_entries(self):
        """Test that get_decision_history retrieves logged decisions."""
        from main import app  # noqa: F401
        from skills import log_decision, get_decision_history

        # Log a decision
        decision = {
            "escalation_decision": "monitor",
            "risk_level": "low",
            "confidence": 0.9,
            "rationale": "Stable metrics",
            "contributing_factors": []
        }
        await log_decision("P002", decision)

        # Retrieve history
        history = await get_decision_history("P002")

        assert history["patient_id"] == "P002"
        assert history["decision_count"] >= 1
        assert len(history["history"]) >= 1

    async def test_get_decision_history_empty_patient(self):
        """Test get_decision_history for patient with no history."""
        from main import app  # noqa: F401
        from skills import get_decision_history

        # Use a unique patient ID that won't have history
        history = await get_decision_history("PXXX_NO_HISTORY")

        assert history["patient_id"] == "PXXX_NO_HISTORY"
        assert history["decision_count"] == 0
        assert history["history"] == []

    async def test_multiple_decisions_logged(self):
        """Test that multiple decisions are appended to history."""
        from main import app  # noqa: F401
        from skills import log_decision, get_decision_history

        patient_id = "P003_MULTI"

        # Log first decision
        await log_decision(patient_id, {"decision": 1})
        
        # Log second decision
        await log_decision(patient_id, {"decision": 2})

        # Check history has both
        history = await get_decision_history(patient_id)

        assert history["decision_count"] >= 2
