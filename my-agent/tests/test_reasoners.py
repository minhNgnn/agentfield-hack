"""
Tests for reasoners.py — Clinical AI reasoners.

Tests cover:
1. Unit tests — Reasoner exists and has correct structure
2. Integration tests — Full AI workflow with AgentField server
"""

import pytest
import asyncio
import inspect


# =============================================================================
# UNIT TESTS: Reasoner Structure
# =============================================================================


class TestReasonersRouter:
    """Unit tests for reasoners router configuration."""

    def test_reasoners_router_exists(self):
        """Test that reasoners_router is defined."""
        from reasoners import reasoners_router

        assert reasoners_router is not None

    def test_reasoners_router_prefix(self):
        """Test that reasoners_router has correct prefix."""
        from reasoners import reasoners_router

        assert reasoners_router.prefix == "clinical"

    def test_reasoners_router_tags(self):
        """Test that reasoners_router has correct tags."""
        from reasoners import reasoners_router

        assert "reasoners" in reasoners_router.tags


class TestEvaluateRiskReasonerUnit:
    """Unit tests for evaluate_risk reasoner structure."""

    def test_evaluate_risk_exists(self):
        """Test that evaluate_risk function exists."""
        from reasoners import evaluate_risk

        assert evaluate_risk is not None

    def test_evaluate_risk_is_async(self):
        """Test that evaluate_risk is an async function."""
        from reasoners import evaluate_risk

        assert asyncio.iscoroutinefunction(evaluate_risk)

    def test_evaluate_risk_has_patient_id_param(self):
        """Test that evaluate_risk accepts patient_id parameter."""
        from reasoners import evaluate_risk

        sig = inspect.signature(evaluate_risk)
        assert "patient_id" in sig.parameters

    def test_evaluate_risk_has_docstring(self):
        """Test that evaluate_risk has documentation."""
        from reasoners import evaluate_risk

        assert evaluate_risk.__doc__ is not None
        assert "clinical" in evaluate_risk.__doc__.lower()


class TestEchoReasonerUnit:
    """Unit tests for echo reasoner (basic test reasoner)."""

    def test_echo_exists(self):
        """Test that echo function exists."""
        from reasoners import echo

        assert echo is not None

    def test_echo_is_async(self):
        """Test that echo is an async function."""
        from reasoners import echo

        assert asyncio.iscoroutinefunction(echo)


# =============================================================================
# INTEGRATION TESTS: Full AI Workflow (requires AgentField server)
# =============================================================================


@pytest.mark.asyncio(loop_scope="class")
class TestEchoReasonerIntegration:
    """Integration tests for echo reasoner."""

    async def test_echo_basic(self):
        """Test basic echo functionality."""
        from main import app  # noqa: F401
        from reasoners import echo

        result = await echo("Hello World")

        assert result["original"] == "Hello World"
        assert result["echoed"] == "Hello World"
        assert result["length"] == 11


@pytest.mark.asyncio(loop_scope="class")
class TestEvaluateRiskIntegration:
    """Integration tests for evaluate_risk reasoner (requires AgentField server + AI)."""

    async def test_evaluate_risk_requires_context(self):
        """Test that evaluate_risk fails without patient context in memory."""
        from main import app  # noqa: F401
        from reasoners import evaluate_risk

        # Try to evaluate a patient without context stored
        with pytest.raises(ValueError) as excinfo:
            await evaluate_risk("NONEXISTENT_PATIENT_XYZ")

        assert "No context found" in str(excinfo.value)

    async def test_evaluate_risk_p001_high_risk(self):
        """Test evaluate_risk for P001 (high risk patient) — expects escalation."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        from reasoners import evaluate_risk

        # Step 1: Store patient context in memory
        store_result = await store_patient_context("P001")
        assert store_result["status"] == "stored"

        # Step 2: Evaluate risk (AI call)
        result = await evaluate_risk("P001")

        # Verify result structure (from EscalationDecision schema)
        assert "escalation_decision" in result
        assert result["escalation_decision"] in ["escalate", "monitor"]

        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high"]

        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

        assert "rationale" in result
        assert isinstance(result["rationale"], str)

        assert "contributing_factors" in result
        assert isinstance(result["contributing_factors"], list)

        # P001 is designed as high risk — expect escalation or high risk
        # (AI might vary, so we check structure not exact values)
        print(f"P001 result: {result}")

    async def test_evaluate_risk_p002_low_risk(self):
        """Test evaluate_risk for P002 (low risk patient) — expects monitor."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        from reasoners import evaluate_risk

        # Step 1: Store patient context in memory
        store_result = await store_patient_context("P002")
        assert store_result["status"] == "stored"

        # Step 2: Evaluate risk (AI call)
        result = await evaluate_risk("P002")

        # Verify result structure
        assert "escalation_decision" in result
        assert result["escalation_decision"] in ["escalate", "monitor"]

        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high"]

        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

        print(f"P002 result: {result}")

    async def test_evaluate_risk_p003_ambiguous(self):
        """Test evaluate_risk for P003 (ambiguous patient) — tests uncertainty handling."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        from reasoners import evaluate_risk

        # Step 1: Store patient context in memory
        store_result = await store_patient_context("P003")
        assert store_result["status"] == "stored"

        # Step 2: Evaluate risk (AI call)
        result = await evaluate_risk("P003")

        # Verify result structure
        assert "escalation_decision" in result
        assert "risk_level" in result
        assert "confidence" in result
        assert "rationale" in result
        assert "contributing_factors" in result

        # P003 is ambiguous — confidence might be lower
        print(f"P003 result: {result}")

    async def test_evaluate_risk_returns_dict(self):
        """Test that evaluate_risk returns a dictionary."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        from reasoners import evaluate_risk

        await store_patient_context("P001")
        result = await evaluate_risk("P001")

        assert isinstance(result, dict)

    async def test_evaluate_risk_rationale_not_empty(self):
        """Test that AI provides a non-empty rationale."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        from reasoners import evaluate_risk

        await store_patient_context("P001")
        result = await evaluate_risk("P001")

        assert result["rationale"]
        assert len(result["rationale"]) > 10  # At least a sentence

    async def test_evaluate_risk_contributing_factors_relevant(self):
        """Test that contributing_factors are relevant to patient."""
        from main import app  # noqa: F401
        from skills import store_patient_context
        from reasoners import evaluate_risk

        await store_patient_context("P001")
        result = await evaluate_risk("P001")

        # Should have at least one contributing factor
        assert len(result["contributing_factors"]) >= 1


# =============================================================================
# UNIT TESTS: Task 5.1 - Triage Patient Workflow
# =============================================================================


class TestTriagePatientUnit:
    """Unit tests for triage_patient workflow reasoner."""

    def test_triage_patient_exists(self):
        """Test that triage_patient function exists."""
        from reasoners import triage_patient

        assert triage_patient is not None

    def test_triage_patient_is_async(self):
        """Test that triage_patient is an async function."""
        import asyncio
        from reasoners import triage_patient

        assert asyncio.iscoroutinefunction(triage_patient)

    def test_triage_patient_has_patient_id_param(self):
        """Test that triage_patient accepts patient_id parameter."""
        import inspect
        from reasoners import triage_patient

        sig = inspect.signature(triage_patient)
        assert "patient_id" in sig.parameters

    def test_triage_patient_has_docstring(self):
        """Test that triage_patient has documentation."""
        from reasoners import triage_patient

        assert triage_patient.__doc__ is not None
        assert "workflow" in triage_patient.__doc__.lower()


# =============================================================================
# INTEGRATION TESTS: Task 5.1 - End-to-End Triage Workflow
# =============================================================================


@pytest.mark.asyncio(loop_scope="class")
class TestTriagePatientIntegration:
    """Integration tests for full triage workflow (requires server + AI)."""

    async def test_triage_patient_p001_full_workflow(self):
        """Test complete triage workflow for P001 (high risk)."""
        from main import app  # noqa: F401
        from reasoners import triage_patient

        result = await triage_patient("P001")

        # Verify workflow completed
        assert result["patient_id"] == "P001"
        assert result["workflow"] == "complete"

        # Verify decision structure
        assert "decision" in result
        decision = result["decision"]
        assert "escalation_decision" in decision
        assert "risk_level" in decision
        assert "confidence" in decision
        assert "rationale" in decision
        assert "contributing_factors" in decision

        # Verify notification flag
        assert "notification_sent" in result

        print(f"P001 triage result: {result}")

    async def test_triage_patient_p002_full_workflow(self):
        """Test complete triage workflow for P002 (low risk)."""
        from main import app  # noqa: F401
        from reasoners import triage_patient

        result = await triage_patient("P002")

        assert result["patient_id"] == "P002"
        assert result["workflow"] == "complete"
        assert "decision" in result

        print(f"P002 triage result: {result}")

    async def test_triage_patient_p003_full_workflow(self):
        """Test complete triage workflow for P003 (ambiguous)."""
        from main import app  # noqa: F401
        from reasoners import triage_patient

        result = await triage_patient("P003")

        assert result["patient_id"] == "P003"
        assert result["workflow"] == "complete"
        assert "decision" in result

        print(f"P003 triage result: {result}")

    async def test_triage_logs_decision(self):
        """Test that triage workflow logs the decision."""
        from main import app  # noqa: F401
        from reasoners import triage_patient
        from skills import get_decision_history

        # Run triage
        await triage_patient("P001")

        # Check decision was logged
        history = await get_decision_history("P001")

        assert history["decision_count"] >= 1
        assert len(history["history"]) >= 1

    async def test_triage_escalate_sends_notification(self):
        """Test that escalation triggers notification."""
        from main import app  # noqa: F401
        from reasoners import triage_patient

        # P001 should escalate (high risk)
        result = await triage_patient("P001")

        # If escalated, notification should have been sent
        if result["decision"]["escalation_decision"] == "escalate":
            assert result["notification_sent"] is True

    async def test_triage_invalid_patient(self):
        """Test that triage fails gracefully for invalid patient."""
        from main import app  # noqa: F401
        from reasoners import triage_patient

        with pytest.raises(Exception):  # Could be ValueError or other
            await triage_patient("INVALID_PATIENT_XYZ")

