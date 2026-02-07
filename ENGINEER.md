# ENGINEER.md — Implementation Plan

## Overview

This document maps PLAN.md to concrete implementation tasks using AgentField's four primitives:
- **Reasoners** — AI judgment calls with typed outputs
- **Skills** — Deterministic code execution
- **Memory** — Shared state across agents
- **Discovery** — Agents find and call each other

Time budget: **3 hours**

---

## Architecture Mapping

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AgentField Control Plane                      │
│                         (af server @ :8080)                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  patient-context    │  │  clinical-reasoner  │  │  notification-audit │
│      Agent          │  │       Agent         │  │       Agent         │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│ Skills:             │  │ Reasoners:          │  │ Skills:             │
│ • normalize_patient │  │ • evaluate_risk     │  │ • send_notification │
│ • extract_trends    │  │                     │  │ • log_decision      │
│                     │  │ Uses: Memory, AI    │  │                     │
│ Writes: Memory      │  │ Calls: Discovery    │  │ Reads: Memory       │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## File Structure

```
my-agent/
├── main.py                      # Agent registration (exists)
├── reasoners.py                 # Clinical Reasoner (modify)
├── skills.py                    # NEW: Deterministic skills
├── schemas.py                   # NEW: Pydantic models for typed outputs
├── data/
│   └── mock_patients.json       # NEW: 3 mock patient scenarios
├── .env                         # API keys (exists)
└── requirements.txt             # Dependencies (exists)
```

---

## Task Checklist

### Phase 1: Foundation (45 min)

#### Task 1.1: Define Pydantic Schemas
**File:** `schemas.py`  
**Uses AgentField:** No (pure Python)  
**Purpose:** Typed outputs for reasoners

```python
# Planned code structure:

class PatientContext(BaseModel):
    """Normalized patient data stored in memory."""
    patient_id: str
    age: int
    conditions: list[str]
    medications: list[str]
    recent_labs: dict[str, float]      # e.g., {"CRP": 12.5, "WBC": 11000}
    vital_trends: dict[str, str]       # e.g., {"heart_rate": "increasing", "bp": "stable"}
    trend_summary: str                 # Human-readable trend description


class EscalationDecision(BaseModel):
    """Structured output from clinical reasoner."""
    escalation_decision: Literal["escalate", "monitor"]
    risk_level: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    contributing_factors: list[str]


class NotificationPayload(BaseModel):
    """Payload for notification skill."""
    patient_id: str
    decision: str
    risk_level: str
    rationale: str
    timestamp: str
```

---

#### Task 1.2: Create Mock Patient Data
**File:** `data/mock_patients.json`  
**Uses AgentField:** No  
**Purpose:** Demo scenarios

```json
// Planned structure:
[
  {
    "patient_id": "P001",
    "name": "Demo Patient A",
    "age": 68,
    "conditions": ["hypertension", "type2_diabetes"],
    "medications": ["metformin", "lisinopril"],
    "labs": {
      "CRP": { "values": [2.1, 4.5, 8.2, 12.5], "dates": ["..."] },
      "WBC": { "values": [7000, 8500, 10000, 11000], "dates": ["..."] }
    },
    "vitals": {
      "heart_rate": { "values": [72, 78, 85, 92], "dates": ["..."] },
      "blood_pressure_systolic": { "values": [130, 135, 142, 148], "dates": ["..."] }
    }
  },
  // ... 2 more patients with different risk profiles
]
```

**Scenarios:**
1. **P001** — High risk: Rising inflammatory markers + vitals trending up → ESCALATE
2. **P002** — Low risk: Stable across all metrics → MONITOR
3. **P003** — Medium risk: Ambiguous signals, uncertainty high → Test confidence scoring

---

#### Task 1.3: Configure AI in main.py
**File:** `main.py`  
**Uses AgentField:** ✅ AIConfig  
**Purpose:** Enable LLM reasoning

```python
# Planned modification:

from agentfield import Agent, AIConfig
import os

app = Agent(
    node_id="clinical-triage",
    agentfield_server="http://localhost:8080",
    version="1.0.0",
    dev_mode=True,
    ai_config=AIConfig(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,  # Lower for more deterministic clinical reasoning
    ),
)
```

---

### Phase 2: Skills Implementation (45 min)

#### Task 2.1: Patient Context Skill — Normalize Data
**File:** `skills.py`  
**Uses AgentField:** ✅ `@app.skill()`  
**Purpose:** Deterministic data transformation

```python
# Planned code:

from agentfield import AgentRouter
from schemas import PatientContext
import json

skills_router = AgentRouter(prefix="patient", tags=["skills"])

@skills_router.skill()
def normalize_patient(patient_id: str) -> dict:
    """
    Load and normalize patient data from mock database.
    
    This is a SKILL (deterministic) — same input always produces same output.
    No AI involved.
    """
    # Load from mock data
    with open("data/mock_patients.json") as f:
        patients = json.load(f)
    
    patient = next((p for p in patients if p["patient_id"] == patient_id), None)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found")
    
    # Extract trends (deterministic logic)
    trends = {}
    for vital_name, vital_data in patient["vitals"].items():
        values = vital_data["values"]
        if len(values) >= 2:
            if values[-1] > values[-2] * 1.1:
                trends[vital_name] = "increasing"
            elif values[-1] < values[-2] * 0.9:
                trends[vital_name] = "decreasing"
            else:
                trends[vital_name] = "stable"
    
    # Build normalized context
    context = PatientContext(
        patient_id=patient["patient_id"],
        age=patient["age"],
        conditions=patient["conditions"],
        medications=patient["medications"],
        recent_labs={k: v["values"][-1] for k, v in patient["labs"].items()},
        vital_trends=trends,
        trend_summary=_generate_trend_summary(trends, patient["labs"])
    )
    
    return context.model_dump()


def _generate_trend_summary(trends: dict, labs: dict) -> str:
    """Deterministic trend summarization."""
    parts = []
    for name, direction in trends.items():
        if direction != "stable":
            parts.append(f"{name} {direction}")
    
    # Check inflammatory markers
    crp = labs.get("CRP", {}).get("values", [])
    if crp and crp[-1] > 10:
        parts.append("elevated CRP")
    
    return "; ".join(parts) if parts else "all metrics stable"
```

---

#### Task 2.2: Patient Context Skill — Store in Memory
**File:** `skills.py`  
**Uses AgentField:** ✅ `@app.skill()`, ✅ `app.memory`  
**Purpose:** Write patient context to shared memory

```python
# Planned code:

@skills_router.skill()
async def store_patient_context(patient_id: str) -> dict:
    """
    Normalize patient data and store in shared memory.
    
    Other agents can read this context via memory.get().
    """
    # Call the normalize skill
    context = normalize_patient(patient_id)
    
    # Store in AgentField shared memory
    # Scope: "session" so it persists across agent calls in this workflow
    await skills_router.app.memory.set(
        key=f"patient:{patient_id}:context",
        value=context,
        scope="session"
    )
    
    return {
        "status": "stored",
        "patient_id": patient_id,
        "memory_key": f"patient:{patient_id}:context"
    }
```

---

### Phase 3: Reasoner Implementation (60 min)

#### Task 3.1: Clinical Reasoner — Risk Evaluation
**File:** `reasoners.py`  
**Uses AgentField:** ✅ `@app.reasoner()`, ✅ `app.ai()`, ✅ `app.memory`  
**Purpose:** AI judgment call with structured output

```python
# Planned code:

from agentfield import AgentRouter
from pydantic import BaseModel, Field
from typing import Literal
from schemas import EscalationDecision

reasoners_router = AgentRouter(prefix="clinical", tags=["reasoners"])


@reasoners_router.reasoner()
async def evaluate_risk(patient_id: str) -> dict:
    """
    Core clinical reasoning — evaluates patient risk and decides escalation.
    
    This is a REASONER (AI judgment) — weighs multiple signals, handles uncertainty.
    
    Example:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_evaluate_risk \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    # 1. Read patient context from shared memory
    context = await reasoners_router.app.memory.get(
        key=f"patient:{patient_id}:context",
        scope="session"
    )
    
    if not context:
        raise ValueError(f"No context found for patient {patient_id}. Run store_patient_context first.")
    
    # 2. Build prompt with patient data
    prompt = f"""
You are a clinical decision support system. Your role is to evaluate whether a patient
should be escalated for immediate clinical review or continue routine monitoring.

You do NOT diagnose. You do NOT prescribe treatment.
You ONLY prioritize clinical attention.

Patient Context:
- Age: {context['age']}
- Conditions: {', '.join(context['conditions'])}
- Medications: {', '.join(context['medications'])}
- Recent Lab Values: {context['recent_labs']}
- Vital Trends: {context['vital_trends']}
- Trend Summary: {context['trend_summary']}

Based on this information, evaluate:
1. Should this patient be escalated for clinical review or continue monitoring?
2. What is the risk level (low/medium/high)?
3. How confident are you in this assessment (0.0-1.0)?
4. What factors contributed to this decision?

Be conservative: when uncertain, prefer escalation over missing a deteriorating patient.
"""

    # 3. AI reasoning with structured output
    result = await reasoners_router.app.ai(
        system="You are a clinical decision support system that prioritizes patient safety.",
        user=prompt,
        schema=EscalationDecision
    )
    
    # 4. Add observability note
    reasoners_router.app.note(
        f"Patient {patient_id}: {result.escalation_decision} (risk={result.risk_level}, confidence={result.confidence})",
        tags=["clinical", "escalation", result.risk_level]
    )
    
    return result.model_dump()
```

---

### Phase 4: Notification & Audit (30 min)

#### Task 4.1: Notification Skill
**File:** `skills.py`  
**Uses AgentField:** ✅ `@app.skill()`  
**Purpose:** Deterministic notification (mocked)

```python
# Planned code:

@skills_router.skill()
def send_notification(patient_id: str, decision: str, risk_level: str, rationale: str) -> dict:
    """
    Send notification to clinical staff (mocked for demo).
    
    This is a SKILL — deterministic, no AI.
    In production: would integrate with hospital paging/alert system.
    """
    from datetime import datetime
    
    notification = {
        "type": "CLINICAL_ESCALATION" if decision == "escalate" else "MONITORING_UPDATE",
        "patient_id": patient_id,
        "risk_level": risk_level,
        "message": rationale,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "sent"  # Mocked
    }
    
    # In production: send to hospital alert system
    print(f"[NOTIFICATION] {notification}")
    
    return notification
```

---

#### Task 4.2: Decision Logging Skill
**File:** `skills.py`  
**Uses AgentField:** ✅ `@app.skill()`, ✅ `app.memory`  
**Purpose:** Store decision for audit trail

```python
# Planned code:

@skills_router.skill()
async def log_decision(patient_id: str, decision: dict) -> dict:
    """
    Log the escalation decision to shared memory for audit trail.
    
    AgentField automatically provides cryptographic audit via W3C DIDs/VCs.
    This skill provides application-level logging.
    """
    from datetime import datetime
    
    log_entry = {
        "patient_id": patient_id,
        "decision": decision,
        "timestamp": datetime.utcnow().isoformat(),
        "logged_by": "clinical-triage"
    }
    
    # Append to decision history in memory
    history_key = f"patient:{patient_id}:decision_history"
    existing = await skills_router.app.memory.get(key=history_key, scope="global") or []
    existing.append(log_entry)
    
    await skills_router.app.memory.set(
        key=history_key,
        value=existing,
        scope="global"  # Persist across sessions
    )
    
    return {"status": "logged", "entry": log_entry}
```

---

### Phase 5: Orchestration via Discovery (30 min)

#### Task 5.1: End-to-End Workflow Reasoner
**File:** `reasoners.py`  
**Uses AgentField:** ✅ `@app.reasoner()`, ✅ `app.call()` (Discovery)  
**Purpose:** Coordinate the full pipeline

```python
# Planned code:

@reasoners_router.reasoner()
async def triage_patient(patient_id: str) -> dict:
    """
    End-to-end clinical triage workflow.
    
    Coordinates:
    1. Patient Context Agent (via skill)
    2. Clinical Reasoner (this agent)
    3. Notification & Audit Agent (via skill)
    
    Example:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    # Step 1: Store patient context in memory
    await reasoners_router.app.call(
        "clinical-triage.patient_store_patient_context",
        input={"patient_id": patient_id}
    )
    
    # Step 2: Run clinical reasoning
    decision = await evaluate_risk(patient_id)
    
    # Step 3: Send notification if escalating
    if decision["escalation_decision"] == "escalate":
        await reasoners_router.app.call(
            "clinical-triage.patient_send_notification",
            input={
                "patient_id": patient_id,
                "decision": decision["escalation_decision"],
                "risk_level": decision["risk_level"],
                "rationale": decision["rationale"]
            }
        )
    
    # Step 4: Log decision for audit
    await reasoners_router.app.call(
        "clinical-triage.patient_log_decision",
        input={
            "patient_id": patient_id,
            "decision": decision
        }
    )
    
    return {
        "patient_id": patient_id,
        "workflow": "complete",
        "decision": decision
    }
```

---

## Demo Script

### Terminal 1: Start Control Plane
```bash
af server
```

### Terminal 2: Start Agent
```bash
cd my-agent
source ../.venv/bin/activate
python main.py
```

### Terminal 3: Run Demo

```bash
# Demo 1: High-risk patient → ESCALATE
curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P001"}}'

# Demo 2: Low-risk patient → MONITOR
curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P002"}}'

# Demo 3: Ambiguous patient → Test confidence
curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P003"}}'
```

### Show in Dashboard
1. Open http://localhost:8080
2. Show workflow DAG visualization
3. Show decision audit trail
4. Show memory contents

---

## AgentField Primitive Usage Summary

| Primitive | Where Used | Purpose |
|-----------|------------|---------|
| **Reasoners** | `evaluate_risk()`, `triage_patient()` | AI judgment calls with typed outputs |
| **Skills** | `normalize_patient()`, `store_patient_context()`, `send_notification()`, `log_decision()` | Deterministic code, no AI |
| **Memory** | Patient context, decision history | Shared state across workflow steps |
| **Discovery** | `app.call()` in `triage_patient()` | Agents coordinate without hardcoded URLs |

---

## What This Replaces

| Before (if-else logic) | After (AgentField) |
|------------------------|-------------------|
| `if crp > 10 and age > 60: alert()` | Reasoner weighs multiple signals contextually |
| Manual trend calculation | Skill extracts trends deterministically |
| Separate database for state | Memory built into platform |
| Hardcoded service URLs | Discovery routes calls automatically |
| "Check the logs" | Cryptographic audit trail (W3C VCs) |

---

## Risk & Contingency

| Risk | Mitigation |
|------|------------|
| LLM API fails | Mock response fallback in `evaluate_risk()` |
| Time overrun | Phase 5 (orchestration) can be simplified to direct calls |
| Demo glitch | Pre-record backup video |
| Memory issues | Use `scope="run"` if session scope causes issues |

---

## Timing Estimate

| Phase | Task | Time |
|-------|------|------|
| 1 | Schemas + Mock Data + AI Config | 45 min |
| 2 | Skills (normalize, store, notify, log) | 45 min |
| 3 | Reasoner (evaluate_risk) | 60 min |
| 4 | Orchestration (triage_patient) | 15 min |
| 5 | Testing & Demo Polish | 15 min |
| **Total** | | **3 hours** |

---

## Definition of Done

- [ ] `af server` runs without errors
- [ ] `python main.py` registers agent successfully
- [ ] All three patient scenarios produce expected outputs
- [ ] Workflow DAG visible in dashboard
- [ ] Decision audit trail accessible
- [ ] 2-minute presentation rehearsed
