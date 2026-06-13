"""
=============================================================================
FILE: agents/report_agent.py
PURPOSE: The SIXTH and FINAL agent in the pipeline. It generates a
         professional incident post-mortem report in Markdown format
         and saves it to the reports/ folder.
=============================================================================

HOW IT WORKS:
- Reads ALL previous agent outputs + the approval decision from state
- If Gemini API is available, asks AI to write a polished report
- If not, fills in a pre-written markdown template
- Saves the report as a .md file in the reports/ folder
- Returns: the final report text

WHEN DOES THIS RUN?
Only AFTER the human clicks "Approve" or "Reject" in the dashboard.
The graph.py file has a conditional edge that skips this agent
when approval_status is "pending". See graph.py for details.
=============================================================================
"""

import os
import re
import random
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def run_report_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Incident Report Agent Node:
    Runs after human operator approval. Aggregates all investigation states
    and generates an enterprise-style Markdown Post-Mortem Report, saving it in the reports/ directory.
    """
    print("\n[Node: Report Agent] Generating post-mortem report...")
    
    # ---- Step 1: Read ALL data from the state ----
    query = state.get("query", "")
    service = state.get("service", "")
    plan = state.get("investigation_plan", "")
    logs_summary = state.get("logs_summary", "")
    metrics_summary = state.get("metrics_summary", "")
    rag_summary = state.get("rag_summary", "")
    diagnosis = state.get("diagnosis", "")
    remediation = state.get("remediation", "")
    approval_status = state.get("approval_status", "approved")
    
    api_key = os.getenv("GEMINI_API_KEY")
    report = ""
    
    # Build a human-readable action status message
    action_taken = "APPROVED - Remediation script applied successfully to production cluster." if approval_status == "approved" else "REJECTED - Operator bypassed recommendation. Manual diagnostics requested."
    
    # ---- Step 2: Try generating report with AI ----
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            You are the SRE Incident Report Generator.
            Create a highly professional, enterprise-grade SRE Incident Report in Markdown for this incident:
            
            Incident query: "{query}"
            Service: {service}
            
            INVESTIGATION DETAIL:
            - Plan: {plan}
            - Log Summary: {logs_summary}
            - Metrics Summary: {metrics_summary}
            - KEDB Recommendations: {rag_summary}
            - Diagnosis: {diagnosis}
            - Proposed Remediation: {remediation}
            - Human Action Taken: {action_taken}
            
            The incident report should follow this structure:
            # Incident Post-Mortem Report: INC-<GENERATE-5-DIGIT-RANDOM-NUMBER>
            
            ## 1. Executive Summary
            
            ## 2. Triggering Event & Symptoms
            
            ## 3. Investigation & Diagnostic Steps Taken
            
            ## 4. Root Cause Analysis (RCA)
            
            ## 5. Remediation & Action Taken
            (Be sure to note if the operator approved or rejected the remediation, and what the outcome was)
            
            ## 6. Long-Term Preventative Measures
            
            Ensure it looks extremely professional, polished, and comprehensive. Do not use placeholders.
            """
            
            response = model.generate_content(prompt)
            report = response.text.strip()
        except Exception as e:
            print(f"[ReportAgent] Gemini API error: {e}. Falling back to rule-based report generation.")
            api_key = None
    
    # ---- Step 3: Fallback — fill in a markdown template ----
    if not api_key or not report:
        inc_num = random.randint(10000, 99999)  # Generate a random incident number
        report = f"""# Incident Post-Mortem Report: INC-{inc_num}

## 1. Executive Summary
On 2026-06-13, a critical operational event impacted the **{service.upper()}** service. The system triggered an SRE investigation pipeline which indexed telemetry metrics, parsed application logs, cross-referenced runbooks, and executed mitigation workflows.
- **Incident Status**: Closed (Resolved)
- **Remediation Decision**: {action_taken}

## 2. Triggering Event & Symptoms
- **Alert/Reported Issue**: *"{query}"*
- **Affected System**: `{service}`
- **Observed Failures**: High HTTP errors returned to clients, causing endpoint failures.

## 3. Investigation & Diagnostic Steps Taken
- **Log File Analysis**: Filtered warning/error statements in `{service}.log`:
  ```
{logs_summary[:300]}...
  ```
- **Telemetry Inspection**: Evaluated hardware and connections in `{service}.json`:
  {metrics_summary}
- **Runbook Similarity Search**: Queried Known Error Database (KEDB) for matches:
  {rag_summary[:300]}...

## 4. Root Cause Analysis (RCA)
**Diagnosis**:
{diagnosis}

## 5. Remediation & Action Taken
- **Proposed Action**:
{remediation}
- **Operator Verdict**: **{approval_status.upper()}**
- **Status Outcome**: {action_taken}

## 6. Long-Term Preventative Measures
1. Implement tighter telemetry monitoring with warnings on pool capacity.
2. Conduct connection leak profiling on the integration code branch.
3. Establish auto-remediation triggers for secondary backup routes.
"""

    # ---- Step 4: Save the report as a markdown file ----
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    reports_dir = os.path.join(project_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)  # Create reports/ folder if it doesn't exist
    
    # Extract the incident ID (e.g., "INC-72516") from the report text
    match = re.search(r"INC-\d+", report)
    inc_id = match.group(0) if match else f"INC-{random.randint(10000, 99999)}"
    
    report_file = os.path.join(reports_dir, f"{inc_id}.md")
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[ReportAgent] Saved incident report to file: {report_file}")
    except Exception as e:
        print(f"[ReportAgent] Failed to write incident report: {e}")
    
    # ---- Step 5: Return the final report to the state ----
    return {
        "final_report": report,
        "current_step": "completed"  # Pipeline is done!
    }
