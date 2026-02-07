# PLAN.md — Clinical Attention Allocation System

## 1. Product Summary

An autonomous backend system that continuously reasons over patient physiological signals to determine when human clinical attention is required. It replaces static threshold-based alerting and manual triage with embedded reasoning that understands context, quantifies uncertainty, and decides—sometimes—to do nothing. Patients are data sources; doctors receive escalation decisions, not advice.

---

## 2. What This System Replaces

| Legacy Approach | This System |
|-----------------|-------------|
| Static thresholds (HR > 120 → alert) | Contextual reasoning over longitudinal patterns |
| Dashboard fatigue requiring manual review | Autonomous attention allocation |
| Fixed decision trees and if-else workflows | Uncertainty-aware embedded reasoning |
| Alert storms with no prioritization | Selective escalation with confidence scores |
| Delayed human attention due to batch processing | Continuous reasoning loop |

The core insight: **the problem is not lack of data—it's lack of continuous reasoning.** Human attention arrives too late because static systems cannot think.

---

## 3. Agent Architecture

Three agents, split by **reasoning responsibility**, not by data field.

### Agent 1: Patient State Reasoner
**Type:** Reasoner  
**Responsibility:** Interpret longitudinal physiological signals and produce a structured state assessment with uncertainty bounds.

- **Inputs:** Time-series wearable data (HRV, sleep stages, activity levels, resting HR trends)
- **Outputs:**
  ```
  {
    "physiological_state": "declining" | "stable" | "recovering",
    "anomaly_detected": bool,
    "uncertainty": 0.0–1.0,
    "signal_summary": string
  }
  ```
- **Key behavior:** Does NOT diagnose. Produces interpretation of what the signals show, not what they mean clinically.

### Agent 2: Risk Context Agent
**Type:** Reasoner  
**Responsibility:** Contextualize the physiological state using patient background to adjust perceived risk.

- **Inputs:** 
  - Output from Patient State Reasoner
  - Static patient context (age, active medications, known conditions)
- **Outputs:**
  ```
  {
    "contextualized_risk": "low" | "moderate" | "elevated" | "high",
    "risk_factors": [string],
    "context_uncertainty": 0.0–1.0,
    "reasoning_trace": string
  }
  ```
- **Key behavior:** A 55-year-old on beta-blockers with declining HRV is different from a 25-year-old athlete. This agent adjusts risk perception, not detection.

### Agent 3: Escalation Synthesizer
**Type:** Reasoner (with conditional skill invocation)  
**Responsibility:** Synthesize all signals and decide: **monitor** or **escalate**.

- **Inputs:**
  - Output from Patient State Reasoner
  - Output from Risk Context Agent
  - (Conditional) Knowledge enrichment results
- **Outputs:**
  ```
  {
    "decision": "continue_monitoring" | "escalate_to_clinician",
    "confidence": 0.0–1.0,
    "escalation_urgency": "routine" | "priority" | "urgent" (if escalating),
    "decision_rationale": string,
    "uncertainty_resolved_by": string | null
  }
  ```
- **Key behavior:** 
  - If combined uncertainty is HIGH, invokes Knowledge Enrichment Skill before deciding.
  - Can decide to do nothing (continue monitoring) with high confidence.
  - Produces structured decision log for every reasoning cycle.

### Skill: Knowledge Enrichment
**Type:** Skill (not an agent)  
**Responsibility:** Reduce uncertainty by consulting domain knowledge when reasoning alone is insufficient.

- **Invoked by:** Escalation Synthesizer (conditionally)
- **Trigger:** Combined uncertainty exceeds threshold (e.g., > 0.6)
- **Implementation:** Mocked lookup returning relevant clinical context
  ```
  query: "beta-blocker + HRV suppression + age > 50"
  response: {
    "relevant_context": "Beta-blockers commonly suppress HRV. Declining HRV in medicated patients may reflect medication effect rather than autonomic dysfunction.",
    "confidence_adjustment": -0.2
  }
  ```
- **Key behavior:** This is a supporting skill, not the product. Minimal implementation, maximum reasoning value.

---

## 4. Data Sources

### Core: Longitudinal Wearable Data
- Heart Rate Variability (HRV) — SDNN, RMSSD trends
- Sleep architecture — deep sleep %, wake episodes
- Activity levels — steps, movement intensity
- Resting heart rate trends

**Treatment:** Time-series reasoning, not point-in-time thresholds. The Patient State Reasoner looks at patterns over 7–14 days.

### Context: Static Patient Information
- Age
- Active medications (especially cardiac-relevant)
- Known conditions (hypertension, diabetes, prior cardiac events)

**Treatment:** Used by Risk Context Agent to adjust interpretation. A "normal" reading for one patient may be concerning for another.

### Optional: User-Provided Signals
- Images (e.g., skin changes, swelling)
- Symptom self-reports

**Treatment:** If included, treated as **noisy supplementary signals**, not diagnoses. An image showing ankle swelling is a risk signal to factor in, not a diagnosis of edema.

**For hackathon scope:** Focus on wearable + context. Image analysis is a stretch goal only.

---

## 5. Role of the Knowledge Graph

### What It Is
A lightweight, conditionally-invoked skill that provides domain knowledge to reduce uncertainty.

### What It Is NOT
- Not a full ontology implementation
- Not a visualization target
- Not the core product

### Implementation Strategy
**Mock it.** Create a simple lookup function that returns pre-written clinical context for 3–5 common query patterns:

```python
MOCK_KG = {
    "beta-blocker+HRV": "Beta-blockers suppress HRV...",
    "age>60+sleep_disruption": "Sleep architecture changes...",
    "diabetes+activity_decline": "Reduced activity in diabetic patients..."
}
```

### Invocation Pattern
1. Escalation Synthesizer detects high uncertainty
2. Constructs query from current context
3. Calls Knowledge Enrichment Skill
4. Incorporates response into final decision
5. Logs that uncertainty was resolved via KG consultation

---

## 6. Trust, Uncertainty, and Auditability

### Uncertainty Handling
Every agent output includes an uncertainty score (0.0–1.0). Uncertainty propagates through the reasoning chain:

1. **Patient State Reasoner** — Signal uncertainty (noisy data, missing values)
2. **Risk Context Agent** — Context uncertainty (incomplete patient history)
3. **Escalation Synthesizer** — Combined uncertainty drives behavior:
   - Low uncertainty → Decide directly
   - High uncertainty → Invoke Knowledge Enrichment first
   - Very high uncertainty → Escalate with explicit "low confidence" flag

### Auditability
Every reasoning cycle produces a structured decision log:

```json
{
  "cycle_id": "uuid",
  "timestamp": "ISO8601",
  "patient_id": "anonymized",
  "inputs": { ... },
  "agent_outputs": {
    "patient_state_reasoner": { ... },
    "risk_context_agent": { ... },
    "escalation_synthesizer": { ... }
  },
  "knowledge_enrichment_invoked": true | false,
  "final_decision": "continue_monitoring" | "escalate_to_clinician",
  "confidence": 0.82,
  "reasoning_trace": "Full chain of reasoning..."
}
```

### AgentField Automatic Audit Trail
**Explicitly note in presentation:** AgentField provides cryptographic audit trails automatically. We do not implement cryptography—we rely on the platform's built-in execution logging and provenance tracking.

### Human-in-the-Loop
- The system **never** takes clinical action
- It **only** allocates attention (escalate or monitor)
- Every escalation includes rationale for clinician review
- Clinicians can provide feedback that improves future reasoning (out of hackathon scope)

---

## 7. Demo Flow

### Setup (Pre-Demo)
- AgentField server running
- Three agents registered: `patient-state-reasoner`, `risk-context-agent`, `escalation-synthesizer`
- Knowledge Enrichment skill available
- Mock patient data loaded (2–3 patient scenarios)

### Demo Scenario 1: Clear Escalation
**Patient:** 62-year-old on beta-blockers, declining HRV trend over 5 days, reduced deep sleep

1. **Trigger:** POST `/api/v1/execute/patient-state-reasoner`
   - Input: 7-day HRV + sleep data
   - Output: `{ "physiological_state": "declining", "uncertainty": 0.3 }`

2. **Coordination:** Escalation Synthesizer invokes Risk Context Agent
   - Input: Physiological state + patient context (age, meds)
   - Output: `{ "contextualized_risk": "elevated", "risk_factors": ["age", "cardiac_medication"] }`

3. **Decision:** Escalation Synthesizer reasons
   - Combined uncertainty: 0.35 (below threshold, no KG needed)
   - Output: `{ "decision": "escalate_to_clinician", "urgency": "priority", "confidence": 0.78 }`

4. **Show:** Structured decision log with full reasoning trace

### Demo Scenario 2: Uncertainty Triggers Knowledge Enrichment
**Patient:** 45-year-old, recently started new medication, ambiguous HRV pattern

1. **Trigger:** POST `/api/v1/execute/patient-state-reasoner`
   - Output: `{ "physiological_state": "uncertain", "uncertainty": 0.7 }`

2. **Coordination:** Risk Context Agent
   - Output: `{ "contextualized_risk": "moderate", "context_uncertainty": 0.5 }`

3. **Decision:** Escalation Synthesizer detects high combined uncertainty
   - **Invokes Knowledge Enrichment Skill**
   - Query: "new_medication + HRV_variability"
   - Response: "New medications commonly cause transient HRV changes..."
   - Uncertainty reduced to 0.4

4. **Final Decision:** `{ "decision": "continue_monitoring", "confidence": 0.72 }`

5. **Show:** Decision log showing KG invocation and uncertainty resolution

### Demo Scenario 3: Deciding to Do Nothing
**Patient:** 28-year-old athlete, normal patterns, stable trends

1. **Full reasoning chain executes**
2. **Output:** `{ "decision": "continue_monitoring", "confidence": 0.95 }`
3. **Point:** The system decided human attention is NOT required. This is a valid, valuable output.

---

## 8. Two-Minute Presentation Outline

### 0:00–0:20 — Problem
> "Clinical attention arrives too late. Not because we lack data—wearables generate continuous signals—but because static thresholds can't think. Alert fatigue is a symptom of systems that don't reason."

### 0:20–0:40 — Insight
> "The solution isn't better thresholds or smarter dashboards. It's embedded reasoning that continuously interprets signals, understands context, quantifies uncertainty, and decides—sometimes—that no action is needed."

### 0:40–1:10 — Architecture (show diagram)
> "Three reasoners, split by responsibility:
> 1. Patient State Reasoner interprets physiological patterns
> 2. Risk Context Agent adjusts for patient background
> 3. Escalation Synthesizer decides: monitor or escalate
>
> When uncertainty is high, a Knowledge Enrichment skill is invoked to reduce it. This is coordination, not a fixed workflow."

### 1:10–1:30 — What We Replaced
> "No if-else logic. No static thresholds. No DAGs. Every decision is reasoned, uncertainty-aware, and logged. AgentField's audit trail provides cryptographic provenance automatically."

### 1:30–1:50 — Alignment with AgentField
> "This is AI-as-backend infrastructure:
> - Reasoners, not chatbots
> - Embedded reasoning, not prompt chains
> - Coordination driven by uncertainty, not predefined flows
> - The system replaces complexity that would otherwise require thousands of lines of business logic."

### 1:50–2:00 — Close
> "Clinical attention should be allocated by reasoning, not rules. This system does that."

---

## 9. Explicit Non-Goals

| Intentionally NOT Building | Reason |
|---------------------------|--------|
| Patient-facing UI | Patients are data sources, not users |
| Doctor workflow UI | Doctors receive decisions, not a product |
| Chat interface | This is infrastructure, not a conversational agent |
| Diagnosis or prescription | System allocates attention, not clinical judgment |
| Full Knowledge Graph | KG is a supporting skill, mocked for demo |
| Image analysis pipeline | Out of scope; wearables are primary |
| Cryptographic implementation | AgentField provides this automatically |
| Fixed DAG workflows | Coordination is dynamic, driven by uncertainty |
| Real-time streaming architecture | Batch/trigger-based reasoning is sufficient for demo |
| Multi-patient prioritization | Single-patient reasoning is the core; fleet management is future work |
| Feedback loop / learning | Valuable but out of hackathon scope |

---

## Appendix: File Structure (Anticipated)

```
my-agent/
├── main.py                     # Agent registration
├── reasoners.py                # Three reasoners defined here
├── skills/
│   └── knowledge_enrichment.py # Mocked KG skill
├── data/
│   ├── mock_patients.json      # 2–3 patient scenarios
│   └── mock_kg.json            # Pre-written knowledge responses
├── .env                        # API keys if needed
└── README.md
```

---

## Appendix: Key Phrases for Judges

- "Embedded reasoning replaces static thresholds"
- "Uncertainty-aware decisions, not binary alerts"
- "Coordination driven by reasoning state, not predefined workflows"
- "The system can decide to do nothing—and that's valuable"
- "AI-as-backend: no UI, no chatbot, just infrastructure"
- "AgentField's audit trail provides accountability automatically"
