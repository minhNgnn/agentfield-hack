"""
Skills module - Deterministic code execution (no AI).

Skills are predictable functions that always produce the same output for the same input.
They handle data transformation, storage, and side effects.
"""

import json
from pathlib import Path
from typing import Optional
from agentfield import AgentRouter
from schemas import PatientContext

# Create router for patient-related skills
skills_router = AgentRouter(prefix="patient", tags=["skills"])


# -----------------------------------------------------------------------------
# Task 2.1: Normalize Patient Data
# -----------------------------------------------------------------------------

@skills_router.skill()
def normalize_patient(patient_id: str) -> dict:
    """
    Load and normalize patient data from mock database.
    
    This is a SKILL (deterministic) — same input always produces same output.
    No AI involved.
    
    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.patient_normalize_patient \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    # Load from mock data
    data_path = Path(__file__).parent / "data" / "mock_patients.json"
    with open(data_path) as f:
        patients = json.load(f)
    
    # Find patient by ID
    patient = next((p for p in patients if p["patient_id"] == patient_id), None)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found")
    
    # Extract trends (deterministic logic)
    trends = {}
    for vital_name, vital_data in patient.get("vitals", {}).items():
        values = vital_data.get("values", [])
        if len(values) >= 2:
            # Compare last two values with 10% threshold
            if values[-1] > values[-2] * 1.1:
                trends[vital_name] = "increasing"
            elif values[-1] < values[-2] * 0.9:
                trends[vital_name] = "decreasing"
            else:
                trends[vital_name] = "stable"
        elif len(values) == 1:
            trends[vital_name] = "stable"
    
    # Extract most recent lab values
    recent_labs = {}
    for lab_name, lab_data in patient.get("labs", {}).items():
        values = lab_data.get("values", [])
        if values:
            recent_labs[lab_name] = values[-1]
    
    # Build normalized context
    context = PatientContext(
        patient_id=patient["patient_id"],
        age=patient["age"],
        conditions=patient.get("conditions", []),
        medications=patient.get("medications", []),
        recent_labs=recent_labs,
        vital_trends=trends,
        trend_summary=_generate_trend_summary(trends, patient.get("labs", {}))
    )
    
    return context.model_dump()


def _generate_trend_summary(trends: dict, labs: dict) -> str:
    """
    Deterministic trend summarization.
    
    Creates a human-readable summary of concerning trends.
    """
    parts = []
    
    # Add non-stable vital trends
    for name, direction in trends.items():
        if direction != "stable":
            # Convert snake_case to readable format
            readable_name = name.replace("_", " ")
            parts.append(f"{readable_name} {direction}")
    
    # Check inflammatory markers (CRP > 10 is elevated)
    crp_data = labs.get("CRP", {})
    crp_values = crp_data.get("values", [])
    if crp_values and crp_values[-1] > 10:
        parts.append(f"elevated CRP ({crp_values[-1]} mg/L)")
    
    # Check WBC (normal: 4500-11000, elevated > 11000)
    wbc_data = labs.get("WBC", {})
    wbc_values = wbc_data.get("values", [])
    if wbc_values and wbc_values[-1] > 11000:
        parts.append(f"elevated WBC ({wbc_values[-1]})")
    
    # Check for concerning lab trends
    for lab_name, lab_data in labs.items():
        values = lab_data.get("values", [])
        if len(values) >= 3:
            # Check if consistently increasing over last 3 readings
            if values[-1] > values[-2] > values[-3]:
                if lab_name not in ["CRP", "WBC"]:  # Already handled above
                    parts.append(f"{lab_name} trending up")
    
    return "; ".join(parts) if parts else "all metrics stable"


# -----------------------------------------------------------------------------
# Task 2.2: Store Patient Context in Memory
# -----------------------------------------------------------------------------

@skills_router.skill()
async def store_patient_context(patient_id: str) -> dict:
    """
    Normalize patient data and store in shared memory.
    
    Other agents can read this context via memory.get().
    This enables the clinical reasoner to access patient data.
    
    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.patient_store_patient_context \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    # Call the normalize skill to get patient context
    context = normalize_patient(patient_id)
    
    # Store in AgentField shared memory (async)
    memory_key = f"patient:{patient_id}:context"
    await skills_router.app.memory.set(memory_key, context)
    
    return {
        "status": "stored",
        "patient_id": patient_id,
        "memory_key": memory_key,
        "context": context
    }


@skills_router.skill()
async def get_patient_context(patient_id: str) -> dict:
    """
    Retrieve patient context from shared memory.
    
    Returns the normalized patient data stored by store_patient_context().
    
    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.patient_get_patient_context \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    memory_key = f"patient:{patient_id}:context"
    context = await skills_router.app.memory.get(memory_key)
    
    if not context:
        raise ValueError(f"No context found for patient {patient_id}. Run store_patient_context first.")
    
    return {
        "status": "found",
        "patient_id": patient_id,
        "memory_key": memory_key,
        "context": context
    }


# -----------------------------------------------------------------------------
# Task 4.1: Notification Skill
# -----------------------------------------------------------------------------

@skills_router.skill()
def send_notification(patient_id: str, decision: str, risk_level: str, rationale: str) -> dict:
    """
    Send notification to clinical staff (mocked for demo).
    
    This is a SKILL — deterministic, no AI.
    In production: would integrate with hospital paging/alert system.
    
    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.patient_send_notification \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001", "decision": "escalate", "risk_level": "high", "rationale": "Rising inflammatory markers"}}'
    """
    from datetime import datetime, timezone
    
    notification = {
        "type": "CLINICAL_ESCALATION" if decision == "escalate" else "MONITORING_UPDATE",
        "patient_id": patient_id,
        "risk_level": risk_level,
        "message": rationale,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "sent"  # Mocked - in production would be actual delivery status
    }
    
    # In production: send to hospital alert system (pager, SMS, etc.)
    print(f"[NOTIFICATION] {notification}")
    
    return notification


# -----------------------------------------------------------------------------
# Task 4.2: Decision Logging Skill
# -----------------------------------------------------------------------------

@skills_router.skill()
async def log_decision(patient_id: str, decision: dict) -> dict:
    """
    Log the escalation decision to shared memory for audit trail.
    
    AgentField automatically provides cryptographic audit via W3C DIDs/VCs.
    This skill provides application-level logging.
    
    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.patient_log_decision \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001", "decision": {"escalation_decision": "escalate", "risk_level": "high"}}}'
    """
    from datetime import datetime, timezone
    
    log_entry = {
        "patient_id": patient_id,
        "decision": decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "logged_by": "clinical-triage"
    }
    
    # Append to decision history in memory
    history_key = f"patient:{patient_id}:decision_history"
    existing = await skills_router.app.memory.get(history_key) or []
    existing.append(log_entry)
    
    await skills_router.app.memory.set(history_key, existing)
    
    return {"status": "logged", "entry": log_entry}


@skills_router.skill()
async def get_decision_history(patient_id: str) -> dict:
    """
    Retrieve decision history for a patient from shared memory.
    
    Returns all logged decisions for audit trail review.
    
    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.patient_get_decision_history \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    history_key = f"patient:{patient_id}:decision_history"
    history = await skills_router.app.memory.get(history_key) or []
    
    return {
        "patient_id": patient_id,
        "decision_count": len(history),
        "history": history
    }

