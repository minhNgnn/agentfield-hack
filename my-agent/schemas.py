"""
Pydantic schemas for typed outputs.

These schemas ensure:
1. Reasoners produce structured, predictable outputs
2. No free-form text — everything is typed
3. Code can consume AI outputs without parsing
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class PatientContext(BaseModel):
    """Normalized patient data stored in memory."""
    
    patient_id: str = Field(description="Unique patient identifier")
    age: int = Field(ge=0, le=150, description="Patient age in years")
    conditions: list[str] = Field(default_factory=list, description="Known medical conditions")
    medications: list[str] = Field(default_factory=list, description="Current medications")
    recent_labs: dict[str, float] = Field(
        default_factory=dict,
        description="Most recent lab values, e.g., {'CRP': 12.5, 'WBC': 11000}"
    )
    vital_trends: dict[str, str] = Field(
        default_factory=dict,
        description="Trend direction for vitals, e.g., {'heart_rate': 'increasing', 'bp': 'stable'}"
    )
    trend_summary: str = Field(
        default="",
        description="Human-readable summary of concerning trends"
    )


class EscalationDecision(BaseModel):
    """Structured output from clinical reasoner."""
    
    escalation_decision: Literal["escalate", "monitor"] = Field(
        description="Whether to escalate to clinical review or continue monitoring"
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        description="Overall risk assessment"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this assessment (0.0-1.0)"
    )
    rationale: str = Field(
        description="Brief explanation grounded in patient data"
    )
    contributing_factors: list[str] = Field(
        default_factory=list,
        description="Key factors that influenced this decision"
    )


class NotificationPayload(BaseModel):
    """Payload for notification skill."""
    
    notification_type: Literal["CLINICAL_ESCALATION", "MONITORING_UPDATE"] = Field(
        description="Type of notification"
    )
    patient_id: str = Field(description="Patient being notified about")
    risk_level: Literal["low", "medium", "high"] = Field(
        description="Risk level for prioritization"
    )
    message: str = Field(description="Notification message content")
    timestamp: str = Field(description="ISO format timestamp")
    status: Literal["pending", "sent", "failed"] = Field(
        default="pending",
        description="Delivery status"
    )


class DecisionLogEntry(BaseModel):
    """Audit log entry for a clinical decision."""
    
    patient_id: str = Field(description="Patient ID")
    decision: EscalationDecision = Field(description="The decision that was made")
    timestamp: str = Field(description="ISO format timestamp")
    logged_by: str = Field(description="Agent that logged this decision")
    workflow_id: Optional[str] = Field(
        default=None,
        description="AgentField workflow ID for traceability"
    )
