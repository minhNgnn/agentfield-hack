# plan.md

## 1. One-sentence product definition

A **clinical decision orchestration backend** that continuously reasons over hospital patient data and coordinates preventive escalation decisions for doctors, replacing brittle rule-based triage logic.

---

## 2. Problem statement

Hospitals rely on static, hard-coded clinical rules and delayed manual review to triage patients.  
As patient volume increases and clinical data becomes richer (labs, vitals, trends over time), these rule-based systems fail to surface early risk signals. Doctors are overloaded, escalation happens too late, and subtle but important patterns are missed — not due to lack of data, but because reasoning across many patients does not scale.

---

## 3. Why this fits AgentField

This problem is fundamentally about **AI embedded in backend systems**, not chat interfaces.

- Clinical triage today is implemented as **if–else logic**
- These rules cannot weigh trade-offs, trends, or uncertainty
- AgentField enables replacing these rules with:
  - **Reasoners** for judgment calls
  - **Skills** for deterministic execution
  - **Memory** for shared patient context
  - **Discovery** for agent coordination without workflows or queues

This system primarily uses **Embedded Reasoning**, with light **Coordination**.

---

## 4. System scope

### What we build
- A backend system that:
  - Ingests structured hospital patient data (mocked)
  - Stores patient context in shared memory
  - Reasons over patient risk
  - Produces preventive escalation recommendations for doctors
- One end-to-end workflow
- One clear AI decision point

### What we explicitly do NOT build
- No diagnoses
- No treatment recommendations
- No patient-facing chatbot
- No full EHR integrations
- No real-time wearable ingestion
- No image analysis
- No large-scale medical knowledge ingestion pipelines

---

## 5. Primary user (ICP)

**Doctors at high-end private hospitals**

They need:
- Early warning signals
- Prioritized attention
- Transparent, auditable recommendations
- Systems that assist clinical judgment rather than replace it

---

## 6. Core use case (single workflow)

### Question the system answers
> “Should this patient be proactively escalated for clinical review right now?”

### Input
- Patient demographics
- Known conditions
- Recent lab biomarkers
- Vital sign trends over time
- Derived trend summaries (e.g. worsening inflammation)

### Reasoning
- Weighs multiple signals together
- Evaluates trends instead of static thresholds
- Accounts for uncertainty

### Output
- A structured escalation recommendation for doctors

---

## 7. Agent architecture

### Agent 1: Patient Context Agent
**Purpose**
- Collects and normalizes patient data
- Writes unified patient context to shared memory

**Primitives used**
- Skills: data normalization
- Memory: patient context storage

---

### Agent 2: Clinical Reasoner Agent (core)
**Purpose**
- Makes the clinical judgment call

**Primitives used**
- Reasoners: evaluates escalation necessity
- Memory: reads patient context
- Discovery: calls other agents by name

This agent replaces hard-coded triage rules with AI judgment.

---

### Agent 3: Notification & Audit Agent
**Purpose**
- Executes deterministic actions after a decision

**Primitives used**
- Skills: notification mock, logging
- Memory: stores decision trace

---

## 8. Reasoner schema (structured output)

The AI does not return free-form text.

Example schema:

```json
{
  "escalation_decision": "escalate | monitor",
  "risk_level": "low | medium | high",
  "confidence": 0.0,
  "rationale": "Short explanation grounded in patient data"
}
```

9. Role of Memory

Shared memory acts as the clinical context layer.

It stores:
	•	Normalized patient state
	•	Trend summaries
	•	Historical decisions and outcomes

Memory enables:
	•	Agents to coordinate without knowing about each other
	•	Reasoning to be grounded in accumulated context
	•	Clear auditability of decisions

No external databases, queues, or configuration are required.

⸻

10. Role of Discovery

Agents do not know where other agents live.

They:
	•	Call each other by name
	•	Share context automatically
	•	Rely on the control plane for routing, retries, and lifecycle

This allows clean coordination without workflows or DAG definitions.

⸻

11. Trust, auditability, and safety

This system:
	•	Never diagnoses
	•	Never prescribes treatment
	•	Never overrides doctors

It only prioritizes attention.

Trust is built through:
	•	Structured outputs
	•	Explicit confidence scores
	•	Clear rationale fields
	•	Logged decision traces

Every recommendation is auditable:
	•	Inputs → reasoning → output
	•	No hidden logic

⸻

12. Demo plan
	1.	Show a mocked patient profile with recent biomarker trends
	2.	Patient Context Agent writes context to shared memory
	3.	Clinical Reasoner Agent is triggered
	4.	Display:
	•	Escalation decision
	•	Risk level
	•	Confidence score
	5.	Notification & Audit Agent logs the decision
	6.	Explain how this replaces rule-based alerts

The demo is backend-first with minimal UI.

-----
13. How this replaces hard-coded logic

Traditional system
```
IF biomarker > threshold AND age > X THEN alert
```

This system
	•	Reasons across:
	•	Multiple biomarkers
	•	Trends over time
	•	Patient context
	•	Produces a judgment rather than a binary rule

This makes triage:
	•	More adaptive
	•	More scalable
	•	More clinically realistic

⸻

14. Final positioning statement

This is not an AI doctor.
It is AI embedded into hospital infrastructure to replace brittle clinical decision logic — safely, transparently, and at scale.