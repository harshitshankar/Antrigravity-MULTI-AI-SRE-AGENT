"""
=============================================================================
FILE: agents/state.py
PURPOSE: Defines the "shared state" — the data structure that gets passed
         between ALL agents in the pipeline.
=============================================================================

WHAT IS STATE?
Think of "state" like a shared notebook that every agent can read and write to.
When the Planner Agent finishes, it writes its findings into this notebook.
Then the Log Agent reads the notebook, adds its own findings, and passes it on.

HOW IT WORKS:
- We use Python's TypedDict to define what fields the notebook has.
- LangGraph reads this definition to know what data flows through the pipeline.
- Each agent function receives this state as input and returns updates to it.

EXAMPLE:
  When you type "Orders API returning 500 errors", the state starts mostly empty.
  After all agents run, it's filled with log analysis, metrics, diagnosis, etc.
=============================================================================
"""

# TypedDict is a Python feature that lets you define a dictionary with specific
# key names and value types. It's like creating a template for a dictionary.
from typing import TypedDict, List, Dict, Any, Optional


class SREAgentState(TypedDict):
    """
    Represents the full state passed between agents in the SRE workflow.
    This state accumulates details as each node completes its execution.
    
    Think of this as a form that gets filled out step by step:
    - First, the user fills in 'query'
    - Then the Planner fills in 'service' and 'investigation_plan'
    - Then the Log Agent fills in 'logs_analyzed' and 'logs_summary'
    - ...and so on until the Report Agent fills in 'final_report'
    """
    
    # --- User Input ---
    query: str                    # What the user typed, e.g. "Orders API returning 500 errors"
    
    # --- Planner Agent Output ---
    service: str                  # Which service is affected: 'orders', 'payment', or 'inventory'
    investigation_plan: str       # The checklist of steps the planner created
    
    # --- Log Agent Output ---
    logs_analyzed: List[str]      # List of individual ERROR/WARN log lines found
    logs_summary: str             # A human-readable summary of what the logs say
    
    # --- Metrics Agent Output ---
    metrics_analyzed: Dict[str, Any]  # Raw metrics data (CPU, memory, error rate, etc.)
    metrics_summary: str              # A human-readable summary of the metrics
    
    # --- RAG/KEDB Agent Output ---
    rag_results: List[Dict[str, Any]]  # Raw search results from the knowledge base
    rag_summary: str                   # Summary of what the knowledge base recommends
    
    # --- Diagnosis Agent Output ---
    diagnosis: str                # The concluded root cause (e.g., "Database pool exhausted")
    remediation: str              # Recommended fix steps (e.g., "Increase pool size")
    
    # --- Human Approval ---
    approval_status: str          # 'pending' = waiting for human, 'approved' or 'rejected'
    
    # --- Report Agent Output ---
    final_report: str             # The complete incident report in Markdown format
    
    # --- Workflow Tracking ---
    current_step: str             # Which agent is currently running (for UI progress display)
    error_message: Optional[str]  # If something goes wrong, the error message is stored here
