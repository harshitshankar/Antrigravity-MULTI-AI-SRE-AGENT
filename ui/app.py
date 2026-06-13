"""
app.py — The Streamlit Front-End Dashboard for the AI SRE Copilot
==================================================================

PURPOSE:
    This file builds the VISUAL DASHBOARD that operators (humans) interact
    with.  It has five tabs:
        1. Dashboard     — shows service health cards (CPU, memory, errors)
        2. Logs View     — displays raw log lines with a keyword filter
        3. Telemetry     — interactive Plotly bar charts of metrics
        4. Investigation — the main AI workflow: trigger an incident, view
                           agent outputs, and approve/reject remediation
        5. Reports       — browse archived post-mortem markdown reports

KEY LIBRARY — Streamlit:
    Streamlit turns a plain Python script into a web app.  Every time the
    user interacts with a widget (button, text input, dropdown), Streamlit
    RE-RUNS the entire script from top to bottom.  That's why you'll see
    "session_state" used to keep data between reruns.

    Vocabulary:
      • st.set_page_config()  — sets the browser tab title, icon, layout
      • st.tabs([...])        — creates a tab bar; each tab is a context
      • st.columns(N)         — creates N side-by-side columns
      • st.expander(label)    — a collapsible section
      • st.session_state      — a dictionary that persists across reruns
      • st.markdown(html, unsafe_allow_html=True) — render raw HTML/CSS
      • st.spinner(msg)       — show a loading spinner while code runs
      • st.rerun()            — force the script to re-execute immediately

OTHER LIBRARIES USED:
    • requests      — makes HTTP calls to our FastAPI backend
    • pandas (pd)   — creates tabular DataFrames for chart data
    • plotly        — renders interactive bar charts and gauges
"""

# ---- Imports ----
import streamlit as st       # The UI framework — every widget starts with st.
import requests              # HTTP client to talk to the FastAPI backend
import json                  # (available but not directly used in this file)
import os                    # Read environment variables (API key check)
from typing import Dict, Any # Type hints
import pandas as pd          # DataFrame library — used to structure chart data
import plotly.graph_objects as go  # Plotly's low-level charting API for bar charts


# ============================================================
# Page Layout & Styling Configuration
# ============================================================
# set_page_config MUST be the first Streamlit command in the script.
# It sets the browser tab title, favicon, layout width, and sidebar state.
# ----------------------------------------------------
# Page Layout & Styling Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="Enterprise AI SRE Copilot",   # Text shown in the browser tab
    page_icon="🛡️",                           # Favicon emoji
    layout="wide",                             # Use the full browser width
    initial_sidebar_state="expanded"           # Sidebar starts open
)

# ---- Global API Endpoint URL ----
# The base URL where our FastAPI server is running.
# Defaults to localhost:8000 but can be overridden via environment variable.
# Global API Endpoint URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# ---- Custom CSS Injection ----
# Streamlit supports injecting raw HTML/CSS via st.markdown with
# unsafe_allow_html=True.  This block styles the entire app with a dark
# "glassmorphism" theme (frosted-glass card effect), custom header colours,
# status badges (green/yellow/red), and workflow node styling.
# Custom CSS Injector for Enterprise Dark Theme & Glassmorphism UI
st.markdown("""
<style>
    /* Global modifications */
    .stApp {
        background-color: #0F121D;
        color: #E2E8F0;
        font-family: 'Outfit', 'Segoe UI', sans-serif;
    }
    
    /* Custom Headers */
    h1, h2, h3 {
        color: #00F0FF !important;
        font-weight: 600 !important;
    }
    
    /* Glassmorphic SRE Card Panels */
    .sre-card {
        background: rgba(26, 32, 53, 0.65);
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .sre-card:hover {
        transform: translateY(-2px);
        border-color: #00F0FF;
    }

    /* System Status Badges */
    .badge-healthy {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid #F59E0B;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }

    /* Workflow Step Node Styling */
    .agent-node {
        background: #1A1F36;
        border-left: 5px solid #00F0FF;
        border-radius: 4px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    .agent-header {
        font-weight: bold;
        color: #00F0FF;
        font-size: 1.1em;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Check API Backend Connection
# ============================================================
# Before rendering anything, we ping the FastAPI /api/system/health endpoint
# to see if the backend is running.  The result is also used by the
# Dashboard, Logs, and Telemetry tabs to display metrics.
# ----------------------------------------------------
# Check API Backend Connection
# ----------------------------------------------------
try:
    # Send a GET request with a 3-second timeout to avoid freezing the UI
    health_response = requests.get(f"{API_BASE_URL}/api/system/health", timeout=3)
    backend_online = health_response.status_code == 200  # True if server responded OK
    system_health = health_response.json() if backend_online else {}  # Parse JSON response
except Exception:
    # If the request fails (server down, network error), mark backend as offline
    backend_online = False
    system_health = {}


# ============================================================
# Sidebar Controls & API Status
# ============================================================
# The sidebar is the narrow panel on the left.  We use it to show:
#   • Connection status (online/offline)
#   • Whether Gemini API key is configured
#   • Quick-copy diagnostic scenario templates
# ----------------------------------------------------
# Sidebar Controls & API Status
# ----------------------------------------------------
with st.sidebar:
    # Display a shield icon at the top of the sidebar
    st.image("https://img.icons8.com/nolan/128/security-shield.png", width=70)
    st.title("SRE Copilot Control")
    st.markdown("---")  # Horizontal divider line
    
    # Render connection status
    # Show a green or red status indicator
    if backend_online:
        st.success("🟢 API Backend Online")       # Green box
    else:
        st.error("🔴 API Backend Offline")         # Red box
        st.warning("Please start the FastAPI server via: `python main.py` in your terminal.")

    # Show environment warning
    # Check if the Gemini API key is set in the environment
    api_key_set = os.getenv("GEMINI_API_KEY") is not None
    if api_key_set:
        st.info("🤖 Gemini Agent Mode: ACTIVE")    # Blue info box
    else:
        st.warning("⚠️ Running in SRE Mock Mode (No Gemini API Key found in env). Fill the key in `.env` to enable LLM nodes.")

    st.markdown("---")
    # Display pre-written alert messages that operators can copy-paste
    # into the Investigation tab to quickly test the system
    st.markdown("### Quick Diagnostic Scenarios")
    st.markdown("Use these templates inside the *Investigation Workflow* tab:")
    
    orders_template = "Orders API is returning 500 errors."
    payment_template = "Payment checkout failing with gateway timeouts."
    inventory_template = "Inventory sync warnings: SKU-8841 stock levels critical."
    
    # st.code renders text in a monospace code block with a copy button
    st.code(orders_template, language="text")
    st.code(payment_template, language="text")
    st.code(inventory_template, language="text")


# ============================================================
# Main Dashboard Layout
# ============================================================
# The page title and subtitle that appear at the very top of the main area.
# ----------------------------------------------------
# Main Dashboard Layout
# ----------------------------------------------------
st.title("🛡️ Enterprise AI SRE Copilot")
st.markdown("Production System Diagnostics and Automated Incident Remediation Dashboard.")

# ---- Create the Top-Level Tab Bar ----
# st.tabs() returns a list of tab context managers.  Content placed inside
# "with tab_dash:" only appears when the user clicks the "📈 Dashboard" tab.
# Create the top-level tab views
tab_dash, tab_logs, tab_metrics, tab_investigation, tab_reports = st.tabs([
    "📈 Dashboard",
    "📝 Logs View",
    "📊 Telemetry",
    "🧠 Investigation Workflow",
    "📁 Incident Reports"
])


# ============================================================
# TAB 1: System Dashboard
# ============================================================
# Shows a health card for each microservice (orders, inventory, payment)
# with CPU, Memory, Error Rate metrics and the most recent log lines.
# ----------------------------------------------------
# TAB 1: System Dashboard
# ----------------------------------------------------
with tab_dash:
    st.subheader("System Health Monitoring")
    
    if not backend_online:
        st.warning("Backend API must be running to display system health metrics.")
    else:
        # Layout columns for services
        # Create 3 columns — one for each service card
        col1, col2, col3 = st.columns(3)
        
        # Loop over each service returned by the /api/system/health endpoint
        for idx, (service, data) in enumerate(system_health.items()):
            col = [col1, col2, col3][idx]  # Pick the correct column
            metrics = data.get("metrics", {})
            status = data.get("status", "HEALTHY")
            
            with col:
                # Build custom HTML card for metrics
                # Choose the CSS class for the status badge based on health status
                badge_class = "badge-healthy" if status == "HEALTHY" else ("badge-warning" if status == "WARNING" else "badge-critical")
                
                # Render a custom HTML card with the service name and status badge
                st.markdown(f"""
                <div class="sre-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <span style="font-size:1.4em; font-weight:bold; text-transform:uppercase;">{service} Service</span>
                        <span class="{badge_class}">{status}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render parameters in grid
                # st.metric shows a big number with an optional delta indicator
                subcol1, subcol2, subcol3 = st.columns(3)
                subcol1.metric("CPU", f"{metrics.get('cpu', 0)}%", delta=None)
                subcol2.metric("Memory", f"{metrics.get('memory', 0)}%", delta=None)
                # Show a positive delta (+18%) for unhealthy services to indicate rising errors
                subcol3.metric("Errors", f"{metrics.get('error_rate', 0)}%", delta="-5%" if status=="HEALTHY" else "+18%")
                
                # Display the last few log lines for quick context
                st.markdown("**Recent Logs (Tail):**")
                logs_tail = data.get("logs_tail", [])
                if logs_tail:
                    # st.code renders text in a scrollable monospace block
                    st.code("\n".join(logs_tail[-4:]), language="log")
                else:
                    st.info("No log entries fetched.")


# ============================================================
# TAB 2: Logs Viewer
# ============================================================
# A dedicated log viewer where operators can select a service and
# filter log lines by keyword (e.g. "ERROR", "HikariPool").
# ----------------------------------------------------
# TAB 2: Logs Viewer
# ----------------------------------------------------
with tab_logs:
    st.subheader("Centralized Service Log Viewer")
    
    if not backend_online:
        st.warning("Backend API must be running to query system log files.")
    else:
        # st.selectbox creates a dropdown menu — operator picks a service dynamically from the API
        services_list = list(system_health.keys()) if system_health else ["orders", "inventory", "payment"]
        service_select = st.selectbox("Select Target Service", services_list)
        # st.text_input creates a single-line text field for the keyword filter
        search_filter = st.text_input("Filter logs by keyword (e.g. ERROR, HikariPool, Stripe)", "")
        
        # Read the logs tail from system health payload
        # Grab the log lines for the selected service from the health data
        logs_list = system_health.get(service_select, {}).get("logs_tail", [])
        
        # Apply the keyword filter (case-insensitive)
        if search_filter:
            filtered_logs = [line for line in logs_list if search_filter.lower() in line.lower()]
        else:
            filtered_logs = logs_list
            
        # Display the filtered log lines
        if filtered_logs:
            st.code("\n".join(filtered_logs), language="log")
        else:
            st.info("No log entries match the current filter.")


# ============================================================
# TAB 3: Telemetry Charts
# ============================================================
# Interactive Plotly bar charts comparing CPU, Memory, and Error Rate
# across all three services.  Plotly is a charting library that creates
# zoomable, hoverable, interactive charts rendered in the browser.
# ----------------------------------------------------
# TAB 3: Telemetry Charts
# ----------------------------------------------------
with tab_metrics:
    st.subheader("System Performance Telemetry")
    
    if not backend_online:
        st.warning("Backend API must be running to load performance telemetry.")
    else:
        # Visualize CPU and Memory with Plotly gauge graphs
        # Create two side-by-side columns for the charts
        chart_col1, chart_col2 = st.columns(2)
        
        # Format dataset
        # Build a list of dicts then convert to a pandas DataFrame.
        # DataFrames are table-like structures that Plotly can easily chart.
        chart_data = []
        for service, info in system_health.items():
            metrics = info.get("metrics", {})
            chart_data.append({
                "Service": service.capitalize(),            # e.g. "Orders"
                "CPU %": metrics.get("cpu", 0),             # CPU usage percentage
                "Memory %": metrics.get("memory", 0),       # Memory usage percentage
                "Error Rate %": metrics.get("error_rate", 0)  # HTTP error rate
            })
        df = pd.DataFrame(chart_data)  # Convert list of dicts → DataFrame table
        
        # ---- Left Column: CPU & Memory Grouped Bar Chart ----
        with chart_col1:
            st.markdown("#### Hardware Resource Comparison")
            fig = go.Figure()  # Create a blank Plotly figure
            # Add a bar trace for CPU utilization (cyan colour)
            fig.add_trace(go.Bar(
                x=df["Service"],
                y=df["CPU %"],
                name="CPU Utilization",
                marker_color="#00F0FF"
            ))
            # Add a second bar trace for Memory utilization (amber colour)
            fig.add_trace(go.Bar(
                x=df["Service"],
                y=df["Memory %"],
                name="Memory Utilization",
                marker_color="#F59E0B"
            ))
            # Style the chart: transparent background, light text, horizontal legend
            fig.update_layout(
                barmode='group',                              # Bars side by side (not stacked)
                paper_bgcolor='rgba(0,0,0,0)',                # Transparent outer area
                plot_bgcolor='rgba(0,0,0,0)',                 # Transparent chart area
                font_color="#E2E8F0",                         # Light grey text
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            # Render the chart in Streamlit, stretching to fill the column width
            st.plotly_chart(fig, use_container_width=True)

        # ---- Right Column: Error Rate Bar Chart ----
        with chart_col2:
            st.markdown("#### HTTP Error Rate telemetry")
            fig_err = go.Figure()
            # Single bar trace for error rates (red colour)
            fig_err.add_trace(go.Bar(
                x=df["Service"],
                y=df["Error Rate %"],
                name="Error Rate",
                marker_color="#EF4444"
            ))
            fig_err.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#E2E8F0"
            )
            st.plotly_chart(fig_err, use_container_width=True)


# ============================================================
# TAB 4: SRE Agent Investigation Workflow
# ============================================================
# This is the CORE tab where the AI agent pipeline is triggered and
# controlled.  The flow is:
#   1. Operator types a symptom/alert message and clicks "Trigger"
#   2. The UI sends a POST to /api/incident/trigger (runs Phase 1)
#   3. Agent outputs (plan, logs, metrics, KEDB, diagnosis) are displayed
#   4. Operator clicks Approve or Reject (runs Phase 2 via /approve)
#   5. Final post-mortem report is displayed
# ----------------------------------------------------
# TAB 4: SRE Agent Investigation Workflow
# ----------------------------------------------------
with tab_investigation:
    st.subheader("Autonomous Diagnostic Agent Console")
    
    # ---- Session State Initialization ----
    # st.session_state is a special dictionary that PERSISTS across Streamlit
    # reruns.  Without it, variables would be lost every time the user clicks
    # a button (because Streamlit re-executes the entire script).
    # Store active session values
    if "incident_id" not in st.session_state:
        st.session_state.incident_id = None       # No incident triggered yet
    if "incident_state" not in st.session_state:
        st.session_state.incident_state = None     # No state data yet

    # ---- Step 1: Input Query to Trigger Incident ----
    # Step 1: Input query to trigger incident
    st.markdown("#### Initiate Incident Diagnostics")
    # Text input where the operator types the observed problem
    query_input = st.text_input(
        "Enter observed symptoms or error message from service alert:",
        placeholder="e.g. Orders API is returning 500 errors."
    )
    
    # Primary-coloured button to kick off the AI investigation
    trigger_btn = st.button("Trigger AI Investigation Workflow", type="primary")
    
    # This block runs when the button is clicked
    if trigger_btn:
        if not backend_online:
            st.error("Cannot trigger investigation: Backend API is offline.")
        elif not query_input.strip():
            st.warning("Please type a valid incident description first.")
        else:
            # st.spinner shows a loading animation while the agents run
            with st.spinner("Executing SRE Agents (Planner, Logs, Metrics, KEDB, Diagnosis)..."):
                try:
                    # Send the query to the FastAPI /api/incident/trigger endpoint
                    res = requests.post(
                        f"{API_BASE_URL}/api/incident/trigger",
                        json={"query": query_input}   # JSON body matching TriggerRequest
                    )
                    if res.status_code == 200:
                        payload = res.json()
                        # Save the incident ID and state into session_state
                        # so they survive the next Streamlit rerun
                        st.session_state.incident_id = payload["incident_id"]
                        st.session_state.incident_state = payload["state"]
                        st.success(f"Incident triggered successfully! Generated ID: {st.session_state.incident_id}")
                    else:
                        st.error(f"Failed to initiate workflow: {res.text}")
                except Exception as ex:
                    st.error(f"Error communicating with backend: {ex}")

    st.markdown("---")  # Horizontal divider

    # ---- Step 2: Show Active Incident Workflow ----
    # This section only renders if an incident has been triggered
    # Step 2: Show active incident workflow
    if st.session_state.incident_id and st.session_state.incident_state:
        state = st.session_state.incident_state
        inc_id = st.session_state.incident_id
        
        st.subheader(f"Incident Board: {inc_id}")
        
        # Display the pipeline nodes and outputs
        # Each st.expander creates a collapsible section showing one agent's output
        
        # 1. Planner Agent — shows the investigation plan and detected service
        # 1. Planner
        with st.expander("📋 Planner Agent Check-list", expanded=True):
            st.markdown(f"**Identified Service:** `{state.get('service', 'unknown')}`")
            st.markdown(state.get("investigation_plan", "No plan created."))
            
        # 2. Log Agent — shows the summary of log analysis
        # 2. Logs
        with st.expander("📝 Logs Agent Analysis Results", expanded=False):
            st.markdown(state.get("logs_summary", "No log findings."))
            
        # 3. Metrics Agent — shows resource utilisation findings
        # 3. Metrics
        with st.expander("📊 Metrics Agent Resource Report", expanded=False):
            st.markdown(state.get("metrics_summary", "No metrics findings."))
            
        # 4. RAG / KEDB Agent — shows matching known-error documents
        # 4. KEDB / RAG
        st.json(list(state.keys()))
        with st.expander("🔍 RAG / Knowledge Base Matches", expanded=False):
            st.markdown(state.get("rag_summary", "No runbooks matching."))
            
        # 5. Diagnosis Agent — shows root cause and proposed remediation
        # 5. Diagnosis
        with st.expander("🧠 Diagnosis Agent Conclusions", expanded=True):
            st.markdown("### Probable Root Cause")
            st.info(state.get("diagnosis", "No diagnosis isolated."))
            
            st.markdown("### Proposed Action Plan")
            st.success(state.get("remediation", "No remediation recommended."))

        # ---- Step 3: Human Approval Gate ----
        # This is the "human-in-the-loop" control.  The AI has proposed a fix,
        # but we need a human to approve it before proceeding.
        # Step 3: Human approval gate
        if state.get("approval_status") == "pending":
            st.warning("⚠️ **OPERATOR APPROVAL NEEDED**: Approve proposed remediation action plan to execute script and compile post-mortem report.")
            
            # Two side-by-side buttons: Approve and Reject
            col_app, col_rej = st.columns(2)
            
            with col_app:
                approve = st.button("✅ Approve Remediation Action", use_container_width=True)
            with col_rej:
                reject = st.button("❌ Reject Remediation Action", use_container_width=True)
                
            # If either button was clicked, send the decision to the backend
            if approve or reject:
                choice = True if approve else False  # True = approved, False = rejected
                with st.spinner("Processing approval and completing incident report..."):
                    try:
                        # POST to /api/incident/{id}/approve with the decision
                        res = requests.post(
                            f"{API_BASE_URL}/api/incident/{inc_id}/approve",
                            json={"approved": choice}   # JSON body matching ApproveRequest
                        )
                        if res.status_code == 200:
                            updated_payload = res.json()
                            # Update session state with the completed state
                            # (now includes final_report and approval_status)
                            st.session_state.incident_state = updated_payload["state"]
                            st.success(f"Incident {inc_id} finalized!")
                            # Force Streamlit to re-run the script so the UI
                            # refreshes and shows the final report section
                            st.rerun()
                        else:
                            st.error(f"Approval transmission failed: {res.text}")
                    except Exception as ex:
                        st.error(f"Communication issue: {ex}")
                        
        else:
            # ---- Post-Approval: Show Final Report ----
            # If approval_status is "approved" or "rejected", display the verdict
            # and the generated post-mortem report.
            # Show approval status
            verdict = state.get("approval_status")
            badge = "✅ APPROVED" if verdict == "approved" else "❌ REJECTED"
            st.markdown(f"**Mitigation Execution Verdict**: **{badge}**")
            
            # Show completed report snippet
            # Render the final post-mortem report (markdown text)
            st.markdown("### Incident Post-Mortem Compilation")
            st.markdown(state.get("final_report", "Generating report..."))


# ============================================================
# TAB 5: Incident Reports Viewer
# ============================================================
# Displays all previously generated post-mortem reports stored as
# markdown files in the reports/ directory.  Operators can browse
# them and download individual reports.
# ----------------------------------------------------
# TAB 5: Incident reports viewer
# ----------------------------------------------------
with tab_reports:
    st.subheader("Archived Incident Incident Reports")
    
    if not backend_online:
        st.warning("Backend API must be running to fetch report archives.")
    else:
        # Load all reports
        # Fetch the list of report files from the FastAPI /api/system/reports endpoint
        try:
            reports_res = requests.get(f"{API_BASE_URL}/api/system/reports")
            if reports_res.status_code == 200:
                reports = reports_res.json()   # List of {filename, content} dicts
            else:
                reports = []
        except Exception:
            reports = []

        if not reports:
            st.info("No compiled post-mortem incident reports found. Trigger and complete an investigation to compile a report.")
        else:
            # Select and display
            # Build a dropdown of report filenames
            report_filenames = [rep["filename"] for rep in reports]
            selected_file = st.selectbox("Select Incident Archive", report_filenames)
            
            # Find and render matching report
            # Find the report dict whose filename matches the selection
            selected_report = next(rep for rep in reports if rep["filename"] == selected_file)
            st.markdown("---")
            # Render the full markdown content of the selected report
            st.markdown(selected_report["content"])
            
            # Download button
            # st.download_button lets the user save the report as a .md file
            st.download_button(
                label="Download Markdown Report",
                data=selected_report["content"],         # The file contents
                file_name=selected_report["filename"],   # Suggested filename
                mime="text/markdown"                      # MIME type for .md files
            )
