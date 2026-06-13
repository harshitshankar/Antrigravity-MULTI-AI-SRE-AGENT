"""
=============================================================================
FILE: agents/log_agent.py
PURPOSE: The SECOND agent in the pipeline. It reads the actual log files
         from the logs/ folder and finds all ERROR and WARNING lines.
=============================================================================

HOW IT WORKS:
- Reads the service name from state (set by the Planner Agent)
- Opens the corresponding .log file (e.g., logs/orders.log)
- Filters for lines containing ERROR, WARN, or "timeout"
- If Gemini API key is available, asks AI to summarize the errors
- If not, creates a simple bullet-point summary
- Returns: the list of error lines + a human-readable summary

IN THE REAL WORLD:
Instead of reading local .log files, this would connect to:
- Splunk (log aggregation platform)
- ELK Stack (Elasticsearch/Logstash/Kibana)
- Datadog Logs
- AWS CloudWatch Logs
See the README for instructions on how to swap in real log sources.
=============================================================================
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def run_log_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log Analysis Agent Node:
    Locates the target service log file, scans for errors/warnings,
    and summarizes log indicators using Gemini or a regex fallback parser.
    """
    print("\n[Node: Log Agent] Analyzing logs...")
    
    # ---- Step 1: Get the service name from the state ----
    # The Planner Agent already identified this and wrote it to state
    service = state.get("service", "orders")
    
    # ---- Step 2: Build the file path to the log file ----
    # os.path.abspath + os.path.join builds the full path to the file
    # __file__ = this script's location, ".." = go up one folder (to project root)
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logs_dir = os.path.join(project_dir, "logs")
    log_file = os.path.join(logs_dir, f"{service}.log")  # e.g., "logs/orders.log"
    
    log_lines = []  # Will store the filtered error/warning lines
    summary = ""    # Will store the human-readable summary
    
    # ---- Step 3: Read the log file and filter for errors ----
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()  # Read ALL lines from the file
                for line in lines:
                    # Only keep lines that contain error indicators
                    # These keywords are common in production logs
                    if "ERROR" in line or "WARN" in line or "timeout" in line.lower():
                        log_lines.append(line.strip())  # .strip() removes whitespace/newlines
            print(f"[LogAgent] Found {len(log_lines)} error/warning log statements in {log_file}")
        except Exception as e:
            err_msg = f"Error reading log file {log_file}: {e}"
            print(f"[LogAgent] {err_msg}")
            summary = err_msg
    else:
        # If the log file doesn't exist, report it
        err_msg = f"Log file for service '{service}' not found at path {log_file}"
        print(f"[LogAgent] {err_msg}")
        summary = err_msg

    # ---- Step 4: Summarize the errors (AI or fallback) ----
    if not summary and log_lines:
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            try:
                # Join the last 20 error lines into one string to send to the AI
                logs_joined = "\n".join(log_lines[-20:])

                prompt = f"""
                You are an SRE Log Analysis Agent.
                The following error/warning logs were captured for the '{service}' service:
 
                {logs_joined}

                Analyze these logs and summarize:
                1. What specific errors/warnings occurred.
                2. When did they start (approximate timeline if available).
                3. Any patterns or immediate insights.

                Keep your summary professional and concise.
                """

                from utils.gemini_helper import generate

                summary = generate(prompt).strip()
            except Exception as e:
                print(f"[LogAgent] Gemini API error: {e}. Falling back to text summary.")
                api_key = None  # Trigger fallback
        
        # ---- Fallback: Create a simple bullet-point summary ----
        if not api_key:
            summary = f"### Log Analysis Summary for '{service}'\n"
            summary += f"Analyzed log entries in `{service}.log`. Found {len(log_lines)} critical events:\n\n"
            for line in log_lines:
                summary += f"- `{line}`\n"  # Format each line as a markdown bullet
    elif not summary:
        summary = f"No error or warning events found in service log `{service}.log`."

    # ---- Step 5: Return updates to the state ----
    return {
        "logs_analyzed": log_lines,    # Raw list of error/warning lines
        "logs_summary": summary,        # Human-readable summary
        "current_step": "logs"          # Track progress
    }
