# 🏥 Clinical Triage Agent

**AI-powered clinical decision support built on [AgentField](https://agentfield.ai)**

An intelligent triage system that evaluates patient risk using structured AI reasoning, automated notifications, and full audit trails — built with four primitives, zero YAML, zero DAGs.

![AgentField](https://img.shields.io/badge/AgentField-v1.0.0-teal)
![Groq](https://img.shields.io/badge/Groq-GPT--OSS--120B-orange)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Tests](https://img.shields.io/badge/Tests-112%20passed-brightgreen)

---

## 🎯 The Problem

Singapore's emergency departments face a growing crisis:

- **Population aging fast** — 1 in 4 Singaporeans will be over 65 by 2030
- **ED wait times averaging 3-4 hours** at peak
- **Manual triage is subjective** — outcomes depend on which nurse is on shift
- **No structured memory** — patient context is lost between handoffs

Traditional rule-based systems are brittle. LLM chatbots hallucinate. Neither provides the structured, auditable decisions that clinical environments require.

## 💡 The Solution

A clinical triage agent that combines **AI judgment** with **deterministic execution** — the AI makes the decision, your code handles everything else.

```
Patient Data → Normalize → AI Risk Assessment → Notification → Audit Log
                  ↕              ↕                    ↕            ↕
               [Skill]      [Reasoner]            [Skill]      [Skill]
                  ↕              ↕                    ↕            ↕
              [Memory] ←――――――――――――――――――――――――――――――――――――――→ [Memory]
```

### What It Does

| Input | Processing | Output |
|-------|-----------|--------|
| Patient ID | Load & normalize clinical data | Structured patient context |
| Lab values, vitals, history | AI evaluates risk with confidence scoring | `ESCALATE` or `MONITOR` decision |
| Risk decision | Conditional notification routing | Alert sent (or not) |
| Full workflow | Immutable audit logging | Complete decision trail |

---

## 🏗️ Architecture — Four AgentField Primitives

This system uses **all four AgentField primitives** — nothing else.

### 🧠 Reasoners — AI Judgment Calls

```python
@reasoners_router.reasoner()
async def evaluate_risk(patient_id: str) -> EscalationDecision:
    """AI evaluates clinical risk with structured output"""
    context = await get_patient_context(patient_id)
    return await reasoners_router.ai(
        system="You are a clinical decision support system...",
        user=f"Evaluate this patient: {context}",
        schema=EscalationDecision,  # Typed output, not free text
    )
```

**Output** — not a string, structured data your code consumes:
```json
{
  "escalation_decision": "escalate",
  "risk_level": "high",
  "confidence": 0.85,
  "rationale": "Elevated CRP and WBC suggest possible infection...",
  "contributing_factors": ["elevated CRP", "rising creatinine", "age 68"]
}
```

### ⚙️ Skills — Deterministic Code Execution

```python
@skills_router.skill()
async def normalize_patient(patient_id: str) -> PatientContext:
    """Load raw data, compute trends, return typed context"""
    # No AI here — pure Python, deterministic, testable

@skills_router.skill()
async def send_notification(patient_id: str, decision: str, ...) -> NotificationPayload:
    """Route alerts based on risk level"""

@skills_router.skill()
async def log_decision(patient_id: str, decision: dict, ...) -> DecisionLogEntry:
    """Immutable audit trail for every clinical decision"""
```

### 🧠 Memory — Shared State Across Scopes

```python
# Store patient context for the workflow
await app.memory.set(f"patient:{patient_id}", context.dict())

# Retrieve it in any skill or reasoner
stored = await app.memory.get(f"patient:{patient_id}")
```

### 🔍 Discovery — Workflow Orchestration

```python
@reasoners_router.reasoner()
async def triage_patient(patient_id: str) -> dict:
    """End-to-end workflow: normalize → store → evaluate → notify → log"""
    context = await app.call("clinical-triage.patient_normalize_patient", ...)
    await app.call("clinical-triage.patient_store_patient_context", ...)
    decision = await app.call("clinical-triage.clinical_evaluate_risk", ...)
    if decision["escalation_decision"] == "escalate":
        await app.call("clinical-triage.patient_send_notification", ...)
    await app.call("clinical-triage.patient_log_decision", ...)
```

---

## 📊 Demo Results

### Three patient scenarios demonstrating different outcomes:

#### P001 — High Risk (Escalate)
> 68yo, hypertension + diabetes + CKD, CRP 12.5 (elevated), rising creatinine

```bash
curl -X POST "http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient" \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P001"}}'
```

```json
{
  "status": "succeeded",
  "result": {
    "patient_id": "P001",
    "workflow": "complete",
    "notification_sent": true,
    "decision": {
      "escalation_decision": "escalate",
      "risk_level": "high",
      "confidence": 0.85,
      "rationale": "Elevated CRP and WBC suggest possible infection, and creatinine is rising in a patient with chronic kidney disease...",
      "contributing_factors": ["elevated CRP", "elevated WBC", "rising creatinine", "chronic kidney disease", "advanced age"]
    }
  },
  "duration_ms": 15163
}
```

#### P002 — Low Risk (Monitor)
> 35yo, seasonal allergies only, all metrics stable and normal

```json
{
  "escalation_decision": "monitor",
  "risk_level": "low",
  "confidence": 0.92,
  "notification_sent": false
}
```

#### P003 — Ambiguous (Conservative Escalation)
> 52yo, hypothyroidism, CRP rising but within range, mild vital increases

```json
{
  "escalation_decision": "escalate",
  "risk_level": "medium",
  "confidence": 0.78,
  "rationale": "While current values are within normal ranges, the upward trend in CRP and vitals warrants proactive review..."
}
```

### Workflow DAGs

The workflow graph dynamically adapts based on AI decisions:

| Patient | Risk | Decision | Nodes | Notification |
|---------|------|----------|-------|-------------|
| P001 | High | Escalate | 6 | ✅ Sent |
| P002 | Low | Monitor | 5 | ❌ Skipped |
| P003 | Medium | Escalate | 6 | ✅ Sent |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [AgentField CLI](https://github.com/Agent-Field/agentfield) installed
- Groq API key

### 1. Clone & Install

```bash
git clone https://github.com/your-username/agentfield-clinical-triage.git
cd agentfield-clinical-triage/my-agent

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_your_key_here
```

### 3. Start AgentField Server

```bash
# Terminal 1 — Control plane
af server
```

### 4. Start the Agent

```bash
# Terminal 2 — Clinical triage agent
cd my-agent
python main.py
```

You should see:
```
✅ Connected to AgentField server — full functionality available
ℹ️ Agent started with AgentField server connection
💓 Enhanced heartbeat sent — Status: ready
```

### 5. Run Triage

```bash
# Terminal 3 — Execute workflow
curl -X POST "http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient" \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P001"}}'
```

### 6. View Dashboard

Open http://localhost:8080 to see workflow graphs, execution history, and agent status.

---

## 🧪 Testing

```bash
cd my-agent

# Run all unit tests (no server required)
python -m pytest tests/ -v --ignore=tests/test_ai_integration.py

# Run integration tests (requires server + agent running)
python -m pytest tests/test_ai_integration.py -v -m integration

# Run everything
python -m pytest tests/ -v
```

**Test coverage: 112 tests across 6 test files**

| Test File | Tests | What It Covers |
|-----------|-------|---------------|
| `test_schemas.py` | 23 | Pydantic model validation, boundaries, serialization |
| `test_mock_patients.py` | 22 | Mock data structure, clinical scenario correctness |
| `test_main_config.py` | 7 | Agent configuration, Groq API setup |
| `test_skills.py` | 27 | Patient normalization, trend computation |
| `test_skills_notification.py` | 14 | Notifications, decision logging, audit history |
| `test_ai_integration.py` | 6 | Live AI calls, structured output, clinical decisions |
| `test_reasoners.py` | 9 | Reasoner registration, schema validation |
| `test_triage_workflow.py` | 4 | End-to-end workflow structure |

---

## 📁 Project Structure

```
my-agent/
├── main.py                 # Agent configuration & entry point
├── schemas.py              # Pydantic models (typed AI outputs)
├── reasoners.py            # AI reasoners (evaluate_risk, triage_patient)
├── skills.py               # Deterministic skills (normalize, notify, log)
├── data/
│   └── mock_patients.json  # 3 clinical scenarios (high/low/ambiguous risk)
├── tests/
│   ├── test_schemas.py
│   ├── test_mock_patients.py
│   ├── test_main_config.py
│   ├── test_skills.py
│   ├── test_skills_notification.py
│   ├── test_reasoners.py
│   ├── test_triage_workflow.py
│   └── test_ai_integration.py
├── .env                    # Groq API key (not committed)
└── requirements.txt
```

---

## 🔧 Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Agent Framework** | [AgentField](https://agentfield.ai) | Four primitives, typed outputs, workflow orchestration |
| **AI Model** | Groq `openai/gpt-oss-120b` | Fast inference, structured JSON output |
| **Typed Outputs** | Pydantic | Schema validation, no parsing, no hoping |
| **Language** | Python 3.9+ | Ecosystem compatibility |
| **Testing** | pytest + pytest-asyncio | Async support, integration testing |

---

## 🌏 Vision

**Phase 1** (Current) — Single-agent triage with mock data

**Phase 2** — Integration with Singapore's [NEHR](https://www.ihis.com.sg/nehr) for real patient records

**Phase 3** — Multi-agent system:
- Triage Agent → Pharmacy Agent → Scheduling Agent
- Cross-agent communication via AgentField Discovery

**Phase 4** — Regional deployment across ASEAN healthcare systems

---

## 📄 License

MIT

---

*Built for the AgentField Hackathon 2026 🏆*