"""
Unit tests for schemas.py

Tests validate:
1. Valid data is accepted
2. Invalid data is rejected with clear errors
3. Default values work correctly
4. Serialization/deserialization works
"""

import pytest
from pydantic import ValidationError
from schemas import (
    PatientContext,
    EscalationDecision,
    NotificationPayload,
    DecisionLogEntry,
)


class TestPatientContext:
    """Tests for PatientContext schema."""

    def test_valid_patient_context(self):
        """Test creating a valid PatientContext."""
        context = PatientContext(
            patient_id="P001",
            age=68,
            conditions=["hypertension", "type2_diabetes"],
            medications=["metformin", "lisinopril"],
            recent_labs={"CRP": 12.5, "WBC": 11000},
            vital_trends={"heart_rate": "increasing", "bp": "stable"},
            trend_summary="heart_rate increasing; elevated CRP",
        )
        
        assert context.patient_id == "P001"
        assert context.age == 68
        assert len(context.conditions) == 2
        assert context.recent_labs["CRP"] == 12.5
        assert context.vital_trends["heart_rate"] == "increasing"

    def test_minimal_patient_context(self):
        """Test PatientContext with only required fields."""
        context = PatientContext(
            patient_id="P002",
            age=25,
        )
        
        assert context.patient_id == "P002"
        assert context.age == 25
        assert context.conditions == []
        assert context.medications == []
        assert context.recent_labs == {}
        assert context.vital_trends == {}
        assert context.trend_summary == ""

    def test_invalid_age_negative(self):
        """Test that negative age is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PatientContext(patient_id="P003", age=-5)
        
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_invalid_age_too_high(self):
        """Test that unrealistic age is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PatientContext(patient_id="P003", age=200)
        
        assert "less than or equal to 150" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ValidationError):
            PatientContext()  # Missing patient_id and age

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization work."""
        original = PatientContext(
            patient_id="P001",
            age=68,
            conditions=["hypertension"],
            recent_labs={"CRP": 12.5},
        )
        
        # Serialize to dict
        data = original.model_dump()
        
        # Deserialize back
        restored = PatientContext(**data)
        
        assert restored == original


class TestEscalationDecision:
    """Tests for EscalationDecision schema."""

    def test_valid_escalate_decision(self):
        """Test valid escalation decision."""
        decision = EscalationDecision(
            escalation_decision="escalate",
            risk_level="high",
            confidence=0.85,
            rationale="Rising inflammatory markers with deteriorating vitals",
            contributing_factors=["elevated CRP", "increasing heart rate", "age > 65"],
        )
        
        assert decision.escalation_decision == "escalate"
        assert decision.risk_level == "high"
        assert decision.confidence == 0.85
        assert len(decision.contributing_factors) == 3

    def test_valid_monitor_decision(self):
        """Test valid monitoring decision."""
        decision = EscalationDecision(
            escalation_decision="monitor",
            risk_level="low",
            confidence=0.92,
            rationale="All metrics stable, no concerning trends",
            contributing_factors=[],
        )
        
        assert decision.escalation_decision == "monitor"
        assert decision.risk_level == "low"

    def test_invalid_decision_value(self):
        """Test that invalid decision values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EscalationDecision(
                escalation_decision="urgent",  # Invalid - not in Literal
                risk_level="high",
                confidence=0.9,
                rationale="Test",
            )
        
        assert "escalation_decision" in str(exc_info.value)

    def test_invalid_risk_level(self):
        """Test that invalid risk levels are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EscalationDecision(
                escalation_decision="escalate",
                risk_level="critical",  # Invalid - not in Literal
                confidence=0.9,
                rationale="Test",
            )
        
        assert "risk_level" in str(exc_info.value)

    def test_confidence_boundary_low(self):
        """Test confidence at lower boundary."""
        decision = EscalationDecision(
            escalation_decision="monitor",
            risk_level="low",
            confidence=0.0,
            rationale="Minimum confidence",
        )
        assert decision.confidence == 0.0

    def test_confidence_boundary_high(self):
        """Test confidence at upper boundary."""
        decision = EscalationDecision(
            escalation_decision="escalate",
            risk_level="high",
            confidence=1.0,
            rationale="Maximum confidence",
        )
        assert decision.confidence == 1.0

    def test_confidence_out_of_range_low(self):
        """Test that confidence below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EscalationDecision(
                escalation_decision="monitor",
                risk_level="low",
                confidence=-0.1,
                rationale="Test",
            )
        
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_confidence_out_of_range_high(self):
        """Test that confidence above 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EscalationDecision(
                escalation_decision="monitor",
                risk_level="low",
                confidence=1.5,
                rationale="Test",
            )
        
        assert "less than or equal to 1" in str(exc_info.value)

    def test_default_contributing_factors(self):
        """Test that contributing_factors defaults to empty list."""
        decision = EscalationDecision(
            escalation_decision="monitor",
            risk_level="low",
            confidence=0.9,
            rationale="Test",
        )
        assert decision.contributing_factors == []


class TestNotificationPayload:
    """Tests for NotificationPayload schema."""

    def test_valid_escalation_notification(self):
        """Test valid clinical escalation notification."""
        notification = NotificationPayload(
            notification_type="CLINICAL_ESCALATION",
            patient_id="P001",
            risk_level="high",
            message="Patient requires immediate clinical review",
            timestamp="2026-02-07T10:30:00Z",
            status="sent",
        )
        
        assert notification.notification_type == "CLINICAL_ESCALATION"
        assert notification.status == "sent"

    def test_valid_monitoring_notification(self):
        """Test valid monitoring update notification."""
        notification = NotificationPayload(
            notification_type="MONITORING_UPDATE",
            patient_id="P002",
            risk_level="low",
            message="Patient status stable, continuing monitoring",
            timestamp="2026-02-07T10:30:00Z",
        )
        
        assert notification.notification_type == "MONITORING_UPDATE"
        assert notification.status == "pending"  # Default

    def test_invalid_notification_type(self):
        """Test that invalid notification types are rejected."""
        with pytest.raises(ValidationError):
            NotificationPayload(
                notification_type="ALERT",  # Invalid
                patient_id="P001",
                risk_level="high",
                message="Test",
                timestamp="2026-02-07T10:30:00Z",
            )

    def test_invalid_status(self):
        """Test that invalid status values are rejected."""
        with pytest.raises(ValidationError):
            NotificationPayload(
                notification_type="CLINICAL_ESCALATION",
                patient_id="P001",
                risk_level="high",
                message="Test",
                timestamp="2026-02-07T10:30:00Z",
                status="delivered",  # Invalid - not in Literal
            )


class TestDecisionLogEntry:
    """Tests for DecisionLogEntry schema."""

    def test_valid_log_entry(self):
        """Test valid decision log entry."""
        decision = EscalationDecision(
            escalation_decision="escalate",
            risk_level="high",
            confidence=0.85,
            rationale="Test rationale",
            contributing_factors=["factor1"],
        )
        
        log_entry = DecisionLogEntry(
            patient_id="P001",
            decision=decision,
            timestamp="2026-02-07T10:30:00Z",
            logged_by="clinical-triage",
            workflow_id="wf-12345",
        )
        
        assert log_entry.patient_id == "P001"
        assert log_entry.decision.escalation_decision == "escalate"
        assert log_entry.logged_by == "clinical-triage"
        assert log_entry.workflow_id == "wf-12345"

    def test_log_entry_without_workflow_id(self):
        """Test log entry with optional workflow_id omitted."""
        decision = EscalationDecision(
            escalation_decision="monitor",
            risk_level="low",
            confidence=0.9,
            rationale="Test",
        )
        
        log_entry = DecisionLogEntry(
            patient_id="P002",
            decision=decision,
            timestamp="2026-02-07T10:30:00Z",
            logged_by="clinical-triage",
        )
        
        assert log_entry.workflow_id is None

    def test_nested_validation(self):
        """Test that nested EscalationDecision is validated."""
        with pytest.raises(ValidationError):
            DecisionLogEntry(
                patient_id="P001",
                decision={
                    "escalation_decision": "invalid",  # Should fail
                    "risk_level": "high",
                    "confidence": 0.9,
                    "rationale": "Test",
                },
                timestamp="2026-02-07T10:30:00Z",
                logged_by="clinical-triage",
            )

    def test_serialization_with_nested_model(self):
        """Test serialization of nested models."""
        decision = EscalationDecision(
            escalation_decision="escalate",
            risk_level="high",
            confidence=0.85,
            rationale="Test",
        )
        
        log_entry = DecisionLogEntry(
            patient_id="P001",
            decision=decision,
            timestamp="2026-02-07T10:30:00Z",
            logged_by="clinical-triage",
        )
        
        # Serialize
        data = log_entry.model_dump()
        
        # Check nested structure
        assert isinstance(data["decision"], dict)
        assert data["decision"]["escalation_decision"] == "escalate"
        
        # Deserialize
        restored = DecisionLogEntry(**data)
        assert restored == log_entry
