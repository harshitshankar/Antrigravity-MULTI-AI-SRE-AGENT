import os
import sys

# Add current folder to sys.path so agents and rag modules can be resolved
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.graph import sre_graph
from agents.report_agent import run_report_agent

def main():
    print("==================================================")
    st_msg = "SRE Agents Integration Verification Test"
    print(st_msg.center(50))
    print("==================================================")
    
    # 1. Setup initial state
    initial_state = {
        "query": "Orders API is returning 500 errors.",
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
    
    # 2. Trigger Phase 1 of LangGraph (up to diagnosis)
    print("\n[Phase 1] Invoking SRE LangGraph workflow...")
    try:
        final_state = sre_graph.invoke(initial_state)
        
        print("\n--- Phase 1 Workflow Results ---")
        print(f"Service Identified  : {final_state.get('service')}")
        print(f"Current Step        : {final_state.get('current_step')}")
        print(f"Approval Status     : {final_state.get('approval_status')}")
        print(f"Logs Filtered Size  : {len(final_state.get('logs_analyzed', []))} entries")
        print(f"Metrics Analyzed Keys: {list(final_state.get('metrics_analyzed', {}).keys())}")
        print(f"KEDB RAG Matches Size: {len(final_state.get('rag_results', []))}")
        print("\n--- Diagnostic Conclusions ---")
        print(f"Root Cause Summary:\n{final_state.get('diagnosis')}")
        print(f"\nProposed Remediation Steps:\n{final_state.get('remediation')}")
        print("--------------------------------")
        
        # Verify that the graph paused correctly
        assert final_state.get("approval_status") == "pending", "Workflow should pause at pending approval status."
        assert final_state.get("current_step") == "diagnosis", "Workflow should finish Phase 1 at the diagnosis node."
        print("\n[SUCCESS] Phase 1 graph execution and pause verified.")
        
        # 3. Simulate Operator Approval
        print("\n[Phase 2] Simulating Operator Approval...")
        approved_state = dict(final_state)
        approved_state["approval_status"] = "approved"
        
        # Run report generation node
        final_report_state = run_report_agent(approved_state)
        approved_state.update(final_report_state)
        
        print("\n--- Phase 2 Workflow Results ---")
        print(f"Final Step          : {approved_state.get('current_step')}")
        print(f"Report Generated    : Yes, {len(approved_state.get('final_report', ''))} characters")
        print("\n[SUCCESS] Incident post-mortem report verified.")
        
        # Verify that the report was written to files
        reports_dir = os.path.join(os.path.dirname(__file__), "reports")
        reports = os.listdir(reports_dir)
        print(f"Saved Reports List: {reports}")
        assert len(reports) > 0, "No markdown files found under reports/."
        print("\n[SUCCESS] Report disk write verified.")
        
        print("\n==================================================")
        print("Integration Test Completed Successfully!")
        print("==================================================")
        
    except Exception as e:
        print(f"\n[FAILURE] Integration test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
