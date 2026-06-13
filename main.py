"""
=============================================================================
FILE: main.py
PURPOSE: The FastAPI backend server — the "brain" that connects the
         Streamlit dashboard (frontend) to the AI agents (backend).
=============================================================================

WHAT IS FastAPI?
FastAPI is a Python framework for building REST APIs (like Express.js for Node).
It lets you create URLs that accept/return JSON data.
Example: POST /api/incident/trigger → triggers the AI pipeline

WHAT ARE API ENDPOINTS?
An "endpoint" is a URL on your server that does something when called.
Think of it like a function you can call over the internet.
- POST = "create something" or "do an action"
- GET = "read something" or "get information"

HOW TO TEST:
1. Start this server: python main.py
2. Open browser: http://127.0.0.1:8000/docs (auto-generated API documentation!)
3. Click "Try it out" on any endpoint to test it interactively

ENDPOINTS IN THIS FILE:
  POST /api/incident/trigger      → Start a new incident investigation
  GET  /api/incident/{id}         → Check status of an investigation
  POST /api/incident/{id}/approve → Approve or reject the fix
  GET  /api/system/health         → Get CPU/memory/errors for all services
  GET  /api/system/reports        → Get all generated incident reports
=============================================================================
"""

import os
import uuid  # Generates unique IDs
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException  # FastAPI framework + error handling
from fastapi.middleware.cors import CORSMiddleware  # Allows cross-origin requests
from pydantic import BaseModel  # For defining request/response data shapes
from dotenv import load_dotenv

# Import our compiled LangGraph pipeline and the report agent
from agents.graph import sre_graph
from agents.report_agent import run_report_agent

load_dotenv()


# ---- Create the FastAPI app ----
app = FastAPI(
    title="Enterprise AI SRE Copilot API",
    description="Backend API simulating AI-driven SRE incident detection, logs/metrics analysis, KEDB lookup, and automated remediation.",
    version="1.0.0"
)

# ---- Configure CORS (Cross-Origin Resource Sharing) ----
# This allows the Streamlit frontend (running on port 8501) to communicate
# with this API server (running on port 8000).
# Without CORS, the browser would block requests between different ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow requests from any origin (for development)
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],       # Allow all headers
)

# ---- In-Memory Data Store ----
# This dictionary stores all incident states. In production, you'd use a
# real database (PostgreSQL, Redis, etc.) instead.
# Key = incident ID (e.g., "INC-A1B2C3")
# Value = the full state dictionary from the agent pipeline
incident_store: Dict[str, Dict[str, Any]] = {}


# ---- Pydantic Models ----
# These define the shape of incoming request data.
# FastAPI uses these to validate requests automatically.
# If someone sends invalid data, FastAPI returns a 422 error.

class TriggerRequest(BaseModel):
    """Shape of the POST body for triggering an incident."""
    query: str  # The incident description, e.g., "Orders API returning 500 errors"

class ApproveRequest(BaseModel):
    """Shape of the POST body for approving/rejecting remediation."""
    approved: bool  # True = approve, False = reject


# ============================================================================
# ENDPOINT 1: Trigger a new incident investigation
# ============================================================================
@app.post("/api/incident/trigger")
async def trigger_incident(req: TriggerRequest):
    """
    🚀 TRIGGER NEW INCIDENT
    
    What it does:
    1. Creates a new incident ID
    2. Runs the LangGraph pipeline: Planner → Logs → Metrics → RAG → Diagnosis
    3. The pipeline STOPS at diagnosis (because approval_status = "pending")
    4. Returns the incident state with all findings
    
    Example request body:
        {"query": "Orders API is returning 500 errors"}
    """
    # Generate a unique incident ID like "INC-A1B2C3"
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    print(f"\n[FastAPI] Initializing incident {incident_id} with SRE query: '{req.query}'")
    
    # Create the initial state with empty fields
    # This is what gets passed through the agent pipeline
    initial_state = {
        "query": req.query,
        "service": "unknown",
        "investigation_plan": "",
        "logs_analyzed": [],
        "logs_summary": "",
        "metrics_analyzed": {},
        "metrics_summary": "",
        "rag_results": [],
        "rag_summary": "",
        "diagnosis": "",
        "remediation": "",
        "approval_status": "pending",
        "final_report": "",
        "current_step": "init",
        "error_message": None
    }
    
    try:
        # ---- Run Phase 1 of the pipeline ----
        # .invoke() runs the graph from start until it hits END
        # Because of our conditional edge, it stops after diagnosis
        # (when approval_status is "pending")
        final_state = sre_graph.invoke(initial_state)
        
        # Store the state so we can resume later (when user approves)
        incident_store[incident_id] = final_state
        
        return {"incident_id": incident_id, "state": final_state}
    except Exception as e:
        print(f"[FastAPI] Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"SRE Agent pipeline failure: {e}")


# ============================================================================
# ENDPOINT 2: Get incident status
# ============================================================================
@app.get("/api/incident/{incident_id}")
async def get_incident(incident_id: str):
    """
    📋 CHECK INCIDENT STATUS
    
    Returns the full state of an incident including all agent findings.
    
    Example: GET /api/incident/INC-A1B2C3
    """
    if incident_id not in incident_store:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return {"incident_id": incident_id, "state": incident_store[incident_id]}


# ============================================================================
# ENDPOINT 3: Approve or reject remediation
# ============================================================================
@app.post("/api/incident/{incident_id}/approve")
async def approve_remediation(incident_id: str, req: ApproveRequest):
    """
    ✅ APPROVE OR REJECT REMEDIATION
    
    What it does:
    1. Updates the approval_status to "approved" or "rejected"
    2. Runs Phase 2 of the pipeline (Report Agent)
    3. Returns the final state including the generated report
    
    Example request body:
        {"approved": true}
    """
    if incident_id not in incident_store:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
        
    state = incident_store[incident_id]
    
    # Check if this incident is actually waiting for approval
    if state.get("approval_status") != "pending":
         return {
             "incident_id": incident_id, 
             "state": state, 
             "message": f"Incident is not pending approval. Current status: '{state.get('approval_status')}'"
         }
    
    # ---- Update the approval decision ----
    state["approval_status"] = "approved" if req.approved else "rejected"
    
    try:
        # ---- Run Phase 2: Generate the incident report ----
        # Instead of re-running the whole graph, we directly call the report agent
        # with the current state (which now has approval_status set)
        report_state_update = run_report_agent(state)
        state.update(report_state_update)  # Merge report into the state
        state["current_step"] = "completed"
        
        # Save the updated state
        incident_store[incident_id] = state
        return {"incident_id": incident_id, "state": state}
    except Exception as e:
        print(f"[FastAPI] Incident report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Incident report compilation failed: {e}")


# ============================================================================
# ENDPOINT 4: System health dashboard data
# ============================================================================
@app.get("/api/system/health")
async def get_system_health():
    """
    📊 SYSTEM HEALTH CHECK
    
    Returns CPU, memory, error rates, and recent logs for all 3 services.
    This data powers the Dashboard and Telemetry tabs in the Streamlit UI.
    """
    project_dir = os.path.abspath(os.path.dirname(__file__))
    metrics_dir = os.path.join(project_dir, "metrics")
    logs_dir = os.path.join(project_dir, "logs")
    
    services = ["orders", "inventory", "payment"]
    health_status = {}
    
    for s in services:
        # ---- Read metrics JSON ----
        m_file = os.path.join(metrics_dir, f"{s}.json")
        metrics = {}
        if os.path.exists(m_file):
            try:
                with open(m_file, "r") as f:
                    metrics = json.load(f)
            except Exception:
                pass
        
        # ---- Read last 12 log lines ----
        l_file = os.path.join(logs_dir, f"{s}.log")
        log_lines = []
        if os.path.exists(l_file):
            try:
                with open(l_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    log_lines = [line.strip() for line in lines[-12:]]  # Last 12 lines
            except Exception:
                pass
        
        # ---- Determine health status based on thresholds ----
        error_rate = metrics.get("error_rate", 0)
        cpu_usage = metrics.get("cpu", 0)
        
        status = "HEALTHY"
        if error_rate > 10 or cpu_usage > 90:
            status = "CRITICAL"
        elif error_rate > 2 or cpu_usage > 75:
            status = "WARNING"
            
        health_status[s] = {
            "metrics": metrics,
            "logs_tail": log_lines,
            "status": status
        }
        
    return health_status


# ============================================================================
# ENDPOINT 5: List all generated reports
# ============================================================================
@app.get("/api/system/reports")
async def get_system_reports():
    """
    📄 LIST ALL INCIDENT REPORTS
    
    Reads all .md files from the reports/ folder and returns their content.
    This powers the "Incident Reports" tab in the Streamlit UI.
    """
    project_dir = os.path.abspath(os.path.dirname(__file__))
    reports_dir = os.path.join(project_dir, "reports")
    
    reports = []
    if os.path.exists(reports_dir):
        try:
            files = os.listdir(reports_dir)
            for f in files:
                if f.endswith(".md"):
                    filepath = os.path.join(reports_dir, f)
                    with open(filepath, "r", encoding="utf-8") as file:
                        content = file.read()
                    reports.append({
                        "filename": f,
                        "content": content
                    })
        except Exception as e:
            print(f"[FastAPI] Error reading reports: {e}")
            
    return reports


if __name__ == "__main__":
    import uvicorn
    # We use 0.0.0.0 as the host so the server can be accessed outside of localhost
    # (e.g. from a Docker container or other devices on the same network).
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
