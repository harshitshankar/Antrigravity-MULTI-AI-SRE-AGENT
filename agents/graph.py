"""
=============================================================================
FILE: agents/graph.py
PURPOSE: This is the "brain wiring" file — it connects all the agents
         together into a sequential pipeline using LangGraph.
=============================================================================

WHAT IS LANGGRAPH?
LangGraph is a Python library that lets you chain AI agents together like
a flowchart. You define:
  1. NODES = individual agents (each is a Python function)
  2. EDGES = connections between agents (who runs after whom)
  3. CONDITIONAL EDGES = "if X then go to A, else go to B"

WHAT DOES THIS FILE DO?
It creates this pipeline:

  planner → logs → metrics → rag → diagnosis →[check approval]→ report → END
                                                      ↓
                                                    (if pending) → END (pause)

The key trick is the CONDITIONAL EDGE after "diagnosis":
- If approval_status == "pending" → STOP the pipeline (return to user)
- If approval_status == "approved" or "rejected" → continue to report

This is how we implement the "Human-in-the-Loop" approval gate!
=============================================================================
"""

# ---- Import LangGraph components ----
# StateGraph: The main class that holds our pipeline definition
# END: A special constant that means "stop the pipeline here"
from langgraph.graph import StateGraph, END

# Import our state definition (the shared data structure)
from agents.state import SREAgentState

# Import all 6 agent functions — each one is a "node" in the graph
from agents.planner import run_planner
from agents.log_agent import run_log_agent
from agents.metrics_agent import run_metrics_agent
from agents.RAG_agent import run_rag_agent
from agents.diagnosis_agent import run_diagnosis_agent
from agents.report_agent import run_report_agent


# ---- Step 1: Create the StateGraph ----
# We pass SREAgentState so LangGraph knows what shape our state dictionary has
workflow = StateGraph(SREAgentState)

# ---- Step 2: Register all agent functions as "nodes" ----
# Each node has a NAME (string) and a FUNCTION (the agent)
# The name is used when defining edges to connect them
workflow.add_node("planner", run_planner)       # Node 1: Planner Agent
workflow.add_node("logs", run_log_agent)         # Node 2: Log Agent
workflow.add_node("metrics", run_metrics_agent)  # Node 3: Metrics Agent
workflow.add_node("rag", run_rag_agent)          # Node 4: RAG/KEDB Agent
workflow.add_node("diagnosis", run_diagnosis_agent)  # Node 5: Diagnosis Agent
workflow.add_node("report", run_report_agent)    # Node 6: Report Agent

# ---- Step 3: Define the execution order (edges) ----
# set_entry_point = which node runs FIRST
workflow.set_entry_point("planner")

# add_edge = "after node A finishes, run node B"
workflow.add_edge("planner", "logs")       # After planner → run logs
workflow.add_edge("logs", "metrics")       # After logs → run metrics
workflow.add_edge("metrics", "rag")        # After metrics → run rag
workflow.add_edge("rag", "diagnosis")      # After rag → run diagnosis
# Note: No direct edge from diagnosis to report!
# Instead, we use a CONDITIONAL edge (see below)


# ---- Step 4: Define the conditional routing function ----
def route_after_diagnosis(state: SREAgentState) -> str:
    """
    This function is called AFTER the diagnosis agent finishes.
    It decides what happens next based on the approval_status.
    
    Returns:
      - "pause" → if we need human approval (stops the pipeline)
      - "report" → if approval has been given (continues to report)
    """
    status = state.get("approval_status", "pending")
    print(f"[Graph Router] Evaluating routing from diagnosis. Approval status: '{status}'")
    
    if status == "pending":
        # The human hasn't approved yet → STOP the pipeline
        # The FastAPI server will hold the state until the user clicks Approve/Reject
        return "pause"
    
    # The human has approved (or rejected) → continue to generate the report
    return "report"


# ---- Step 5: Add the conditional edge ----
# This tells LangGraph: "After diagnosis, call route_after_diagnosis() to decide
# what to do next. If it returns 'pause', go to END. If 'report', go to report node."
workflow.add_conditional_edges(
    "diagnosis",               # Source node (runs after diagnosis)
    route_after_diagnosis,     # Function that decides the next step
    {
        "pause": END,          # If function returns "pause" → stop pipeline
        "report": "report"     # If function returns "report" → go to report node
    }
)

# ---- Step 6: Connect report node to END ----
workflow.add_edge("report", END)  # After report → pipeline is done

# ---- Step 7: Compile the graph ----
# .compile() takes all our nodes and edges and creates an executable pipeline
# This "sre_graph" object can be called with .invoke(state) to run the pipeline
sre_graph = workflow.compile()

# Now other files (like main.py) can import sre_graph and call:
#   result = sre_graph.invoke(initial_state)
# This will run all agents in order and return the final state
