from agentfield import AgentRouter

from schemas import EscalationDecision

# Group related reasoners with a router
reasoners_router = AgentRouter(prefix="clinical", tags=["reasoners"])


@reasoners_router.reasoner()
async def echo(message: str) -> dict:
    """
    Simple echo reasoner - works without AI configured.

    Example usage:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_echo \
      -H "Content-Type: application/json" \
      -d '{"input": {"message": "Hello World"}}'
    """
    return {
        "original": message,
        "echoed": message,
        "length": len(message)
    }


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
    context = await reasoners_router.app.memory.get(f"patient:{patient_id}:context")

    if not context:
        raise ValueError(
            f"No context found for patient {patient_id}. Run store_patient_context first."
        )

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

Respond with JSON matching this structure:
{{
    "escalation_decision": "escalate" or "monitor",
    "risk_level": "low" or "medium" or "high",
    "confidence": 0.0 to 1.0,
    "rationale": "explanation of decision",
    "contributing_factors": ["factor1", "factor2", ...]
}}

Be conservative: when uncertain, prefer escalation over missing a deteriorating patient.
"""

    # 3. AI reasoning with structured output
    result = await reasoners_router.app.ai(
        system="You are a clinical decision support system that prioritizes patient safety. Always respond with valid JSON.",
        user=prompt,
        schema=EscalationDecision,
    )

    # 4. Add observability note
    reasoners_router.app.note(
        f"Patient {patient_id}: {result.escalation_decision} (risk={result.risk_level}, confidence={result.confidence})",
        tags=["clinical", "escalation", result.risk_level],
    )

    return result.model_dump()


# -----------------------------------------------------------------------------
# Task 5.1: End-to-End Workflow Reasoner
# -----------------------------------------------------------------------------

@reasoners_router.reasoner()
async def triage_patient(patient_id: str) -> dict:
    """
    End-to-end clinical triage workflow.

    Coordinates:
    1. Patient Context Agent (via skill) - store patient data in memory
    2. Clinical Reasoner (this agent) - AI risk evaluation
    3. Notification & Audit Agent (via skill) - notify and log

    This demonstrates AgentField's Discovery primitive — agents coordinate
    without hardcoded URLs.

    Example:
    curl -X POST http://localhost:8080/api/v1/execute/clinical-triage.clinical_triage_patient \
      -H "Content-Type: application/json" \
      -d '{"input": {"patient_id": "P001"}}'
    """
    # Import skills for direct calls (same agent)
    from skills import store_patient_context, send_notification, log_decision

    # Step 1: Store patient context in memory
    reasoners_router.app.note(
        f"Starting triage workflow for patient {patient_id}",
        tags=["workflow", "triage", "start"],
    )

    await store_patient_context(patient_id)

    # Step 2: Run clinical reasoning (AI judgment)
    decision = await evaluate_risk(patient_id)

    # Step 3: Send notification if escalating
    notification = None
    if decision["escalation_decision"] == "escalate":
        notification = send_notification(
            patient_id=patient_id,
            decision=decision["escalation_decision"],
            risk_level=decision["risk_level"],
            rationale=decision["rationale"],
        )

    # Step 4: Log decision for audit trail
    await log_decision(patient_id, decision)

    # Step 5: Complete workflow
    reasoners_router.app.note(
        f"Triage workflow complete for patient {patient_id}: {decision['escalation_decision']}",
        tags=["workflow", "triage", "complete", decision["risk_level"]],
    )

    return {
        "patient_id": patient_id,
        "workflow": "complete",
        "decision": decision,
        "notification_sent": notification is not None,
    }
