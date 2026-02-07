# 🎬 Demo Script — Clinical Triage AI System

**Duration:** 2 minutes  
**Target:** Technical demonstration of AgentField primitives  
**Prerequisites:** AgentField server running, agent registered

---

## Setup Before Recording

Run these commands in separate terminals before starting the recording:

```bash
# Terminal 1: AgentField Control Plane
af server

# Terminal 2: Clinical Triage Agent
cd my-agent && source ../.venv/bin/activate && python main.py
```

Verify both are running:
```bash
curl -s http://localhost:8080/health && curl -s http://localhost:8001/health
```

Have these windows ready:
1. **Terminal** — for curl commands
2. **Browser Tab 1** — AgentField Dashboard (http://localhost:8080)
3. **VS Code** — with `reasoners.py` and `skills.py` open

---

## Demo Script (2:00)

### 🎬 Scene 1: Introduction (0:00 - 0:15)

**[SHOW: VS Code with project structure visible]**

> "This is a clinical triage AI system built with AgentField. It demonstrates all four primitives: Reasoners for AI judgment, Skills for deterministic logic, Memory for shared state, and Discovery for agent coordination."

**ACTION:** Briefly show the file tree:
```
my-agent/
├── main.py          ← Agent config with Groq AI
├── reasoners.py     ← AI judgment calls
├── skills.py        ← Deterministic operations
├── schemas.py       ← Typed Pydantic outputs
└── data/mock_patients.json
```

---

### 🎬 Scene 2: High-Risk Patient — ESCALATE (0:15 - 0:50)

**[SHOW: Terminal]**

> "Let's triage a high-risk patient. P001 is a 68-year-old with diabetes, hypertension, and rising inflammatory markers."

**ACTION:** Run the command:
```bash
curl -X POST "http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient" \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P001"}}'
```

**[SHOW: JSON response in terminal]**

> "The AI analyzes the patient context — age, conditions, lab trends — and returns a structured decision. High risk, escalate, 85% confidence. Notice this isn't free-form text — it's typed JSON that code can consume directly."

**Highlight in response:**
```json
{
  "escalation_decision": "escalate",
  "risk_level": "high",
  "confidence": 0.85,
  "rationale": "Rising CRP, worsening kidney function...",
  "contributing_factors": ["elevated_CRP", "creatinine_trending_up", "age_68"]
}
```

**[SHOW: AgentField Dashboard → Workflow Executions]**

> "In the AgentField dashboard, we see the workflow DAG — 6 nodes executed. The AI reasoner called skills to normalize data, store context in memory, then made its decision and triggered a notification."

**ACTION:** Click on the workflow to show DAG visualization with nodes:
- `normalize_patient` (Skill)
- `store_patient_context` (Skill + Memory)
- `evaluate_risk` (Reasoner + AI)
- `send_notification` (Skill)
- `log_decision` (Skill + Memory)

---

### 🎬 Scene 3: Low-Risk Patient — MONITOR (0:50 - 1:15)

**[SHOW: Terminal]**

> "Now a low-risk patient. P002 is 35 years old with stable vitals and normal labs."

**ACTION:** Run the command:
```bash
curl -X POST "http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient" \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P002"}}'
```

**[SHOW: JSON response]**

> "The AI correctly identifies this as low risk — no escalation needed. Notice the confidence is high because the signals are unambiguous."

**Highlight:**
```json
{
  "escalation_decision": "monitor",
  "risk_level": "low",
  "confidence": 0.92
}
```

**[SHOW: Dashboard — Workflow Executions]**

> "This workflow has only 5 nodes — no notification was sent because the decision was 'monitor'. This is conditional logic in the orchestrator."

---

### 🎬 Scene 4: Ambiguous Patient — Confidence Scoring (1:15 - 1:40)

**[SHOW: Terminal]**

> "The interesting case: P003 has borderline signals. CRP is rising but still within range. This tests the AI's uncertainty quantification."

**ACTION:** Run the command:
```bash
curl -X POST "http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient" \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P003"}}'
```

**[SHOW: JSON response]**

> "Medium risk, but notice the confidence is lower — around 70%. The AI is saying 'I'm less certain here.' Our prompt instructs it to be conservative, so it escalates to avoid missing a deteriorating patient."

**Highlight:**
```json
{
  "escalation_decision": "escalate",
  "risk_level": "medium",
  "confidence": 0.70,
  "rationale": "CRP trending upward though within range..."
}
```

---

### 🎬 Scene 5: Code Walkthrough (1:40 - 1:55)

**[SHOW: VS Code with `reasoners.py` open]**

> "The key is separation of concerns. Skills handle deterministic logic — data normalization, memory storage. Reasoners handle AI judgment with typed Pydantic outputs."

**ACTION:** Scroll to show `evaluate_risk` function:
```python
@reasoners_router.reasoner()
async def evaluate_risk(patient_id: str) -> dict:
    # 1. Read from shared memory
    context = await reasoners_router.app.memory.get(f"patient:{patient_id}:context")
    
    # 2. AI reasoning with structured output
    result = await reasoners_router.app.ai(
        system="You are a clinical decision support system...",
        user=prompt,
        schema=EscalationDecision  # ← Pydantic model enforces structure
    )
```

> "The `app.ai()` call uses Groq's LLaMA 70B model with a Pydantic schema — ensuring the output is always valid, typed JSON."

---

### 🎬 Scene 6: Wrap-up (1:55 - 2:00)

**[SHOW: Dashboard with all 3 workflows visible]**

> "Three patients, three different outcomes. AgentField handles orchestration, memory, and audit trails automatically. The AI makes the judgment calls, skills handle the deterministic work."

**ACTION:** Point to the workflow list showing:
- P001: 6 nodes, ~15s, **escalate**
- P002: 5 nodes, ~2s, **monitor**  
- P003: 6 nodes, ~10s, **escalate** (medium confidence)

---

## Backup Commands (if live demo fails)

```bash
# Simple health check
curl -s http://localhost:8080/health | jq .

# Single skill call (faster, no AI)
curl -X POST "http://localhost:8080/api/v1/execute/clinical-triage.patient_normalize_patient" \
  -H "Content-Type: application/json" \
  -d '{"input": {"patient_id": "P001"}}' | jq .

# Check agent registration
curl -s http://localhost:8080/api/v1/agents | jq '.[] | {id: .node_id, skills: .skills | length}'
```

---

## Key Technical Points to Emphasize

| AgentField Primitive | Where Shown | What It Does |
|---------------------|-------------|--------------|
| **Reasoners** | `evaluate_risk()` | AI judgment with typed Pydantic output |
| **Skills** | `normalize_patient()`, `send_notification()` | Deterministic code, no AI |
| **Memory** | `app.memory.set()` / `get()` | Shared state across workflow steps |
| **Discovery** | Orchestrator calls skills | Agents find each other without hardcoded URLs |

---

## What NOT to Say in Technical Demo

- ❌ "This will replace doctors" (not the point)
- ❌ Business model or market size (separate presentation)
- ❌ Compliance details (DID/VC — mention briefly if time)

## What TO Emphasize

- ✅ Typed outputs prevent AI hallucination in structure
- ✅ Skills vs Reasoners separation (deterministic vs judgment)
- ✅ Memory enables stateful workflows
- ✅ Confidence scoring for uncertainty quantification
- ✅ Conditional workflow paths (notify only if escalating)
