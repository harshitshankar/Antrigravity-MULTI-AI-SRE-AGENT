"""
=============================================================================
FILE: agents/diagnosis_agent.py
PURPOSE: The FIFTH agent in the pipeline. It combines ALL findings from
         the previous agents (logs, metrics, KEDB) and determines:
         1. The most likely ROOT CAUSE of the incident
         2. Specific REMEDIATION steps to fix it
=============================================================================

HOW IT WORKS:
- Reads the logs summary, metrics summary, and KEDB summary from state
- If Gemini API is available, sends all findings to AI for a comprehensive diagnosis
- If not, uses service-specific rule-based diagnosis templates
- Sets approval_status to "pending" — this is what triggers the human approval gate!

WHY DOES IT SET approval_status = "pending"?
The LangGraph workflow has a conditional edge after this agent (see graph.py).
When the graph sees "pending", it STOPS the pipeline and returns control
to the FastAPI server. The user then clicks Approve/Reject in the dashboard,
which resumes the pipeline and runs the Report Agent.
=============================================================================
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def run_diagnosis_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diagnosis Agent Node:
    Aggregates log findings, metric alerts, and RAG runbook resolutions.
    Employs Gemini or a rule-based engine to isolate the root cause and propose remediations,
    transitioning the approval status to 'pending' to prompt SRE human approval.
    """
    print("\n[Node: Diagnosis Agent] Diagnosing root cause...")
    
    # ---- Step 1: Read all previous agent outputs from the state ----
    query = state.get("query", "")
    service = state.get("service", "")
    logs_summary = state.get("logs_summary", "")      # From Log Agent
    metrics_summary = state.get("metrics_summary", "")  # From Metrics Agent
    rag_summary = state.get("rag_summary", "")          # From RAG Agent
    
    api_key = os.getenv("GEMINI_API_KEY")
    diagnosis = ""
    remediation = ""
    
    # ---- Step 2: Try using AI to diagnose (recommended) ----
    if api_key:
        try:
         
            # This is the most important prompt in the system!
            # We feed ALL the findings from previous agents to the AI
            # and ask it to determine the root cause + fix
            prompt = f"""
            You are the Lead SRE Diagnosis Agent.
            An incident occurred on the '{service}' service.
            Incident Report: "{query}"
            
            Here are the findings from our telemetry and knowledge base investigations:
            
            1. LOG ANALYSIS:
            {logs_summary}
            
            2. TELEMETRY METRICS:
            {metrics_summary}
            
            3. RUNBOOKS / KEDB MATCHES:
            {rag_summary}
            
            Based on all these findings:
            1. Determine the probable Root Cause.
            2. Suggest concrete, actionable Remediation Steps (e.g., scale pods, restart database connection pool, apply rate limiting, failover payments).
            
            Provide your output in this exact format:
            ROOT CAUSE:
            <description of the root cause>
            
            REMEDIATION:
            <actionable steps to resolve the issue>
            """
            from utils.gemini_helper import generate

            response_text = generate(prompt).strip()
            
            # ---- Parse the AI's response into separate diagnosis and remediation ----
            if "REMEDIATION:" in response_text:
                parts = response_text.split("REMEDIATION:")
                root_cause_part = parts[0].replace("ROOT CAUSE:", "").strip()
                remediation_part = parts[1].strip()
            else:
                root_cause_part = response_text.replace("ROOT CAUSE:", "").strip()
                remediation_part = "No remediation suggested by LLM."
                
            diagnosis = root_cause_part
            remediation = remediation_part
            
        except Exception as e:
            print(f"[DiagnosisAgent] Gemini API error: {e}. Falling back to rule-based engine.")
            api_key = None
    
    # ---- Step 3: Fallback — rule-based diagnosis for each service ----
    # These are pre-written templates based on common issues for each service
    if not api_key or not diagnosis:
        if service == "orders":
            diagnosis = "HikariPool database connection pool exhaustion in Orders API. All 100 available connections are in use, with client requests waiting up to 30000ms, triggering HTTP 500 response codes."
            remediation = """1. **Scale Connection Pool**: Increase Hikari pool size parameters temporarily to handle spike:
   `spring.datasource.hikari.maximum-pool-size=150`
2. **Trace Leaks**: Enable connection leak logging detection threshold:
   `spring.datasource.hikari.leak-detection-threshold=2000`
3. **Restart Service**: Perform a rolling restart of the Orders API pods to forcibly release connection locks."""
        elif service == "payment":
            diagnosis = "Read timeout to the Stripe payment API gateway (api.stripe.com) resulting in 504 errors on checkout payments. Looks like Stripe is experiencing external delays."
            remediation = """1. **Check Provider Status**: Verify vendor service status on status.stripe.com.
2. **Trip Circuit Breaker**: Trip the client circuit breaker for Stripe integration to fail-fast.
3. **Switch Gateway**: Route newly initiated credit card checkouts through backup PayPal/Adyen pipeline."""
        elif service == "inventory":
            diagnosis = "Stock levels are warning low for SKU-8841. DB transactions are healthy, but physical inventory is low."
            remediation = """1. **Trigger Reorder**: Automatically create a restock invoice order in ERP.
2. **Cache Data**: Enable edge-caching on inventory level check APIs to reduce read loads."""
        else:
            diagnosis = f"General system anomaly detected on service {service}."
            remediation = "1. Rolling restart application pods.\n2. Enable debug-level trace logs in configuration manager."

    print(f"[Diagnosis] Concluded Root Cause: {diagnosis[:80]}...")
    
    # ---- Step 4: Return updates to the state ----
    # IMPORTANT: We set approval_status = "pending" here!
    # This is the trigger that makes the LangGraph pipeline PAUSE
    # and wait for human approval before continuing to the report.
    return {
        "diagnosis": diagnosis,
        "remediation": remediation,
        "approval_status": "pending",  # ← THIS TRIGGERS THE HUMAN APPROVAL GATE
        "current_step": "diagnosis"
    }
