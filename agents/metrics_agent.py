"""
=============================================================================
FILE: agents/metrics_agent.py
PURPOSE: The THIRD agent in the pipeline. It reads system metrics
         (CPU, memory, error rate, etc.) from JSON files and checks
         if any values exceed safe thresholds.
=============================================================================

HOW IT WORKS:
- Reads the service name from state
- Opens the corresponding .json file (e.g., metrics/orders.json)
- If Gemini API is available, asks AI to interpret the metrics
- If not, uses simple if/else threshold rules:
    - CPU > 80%      → WARNING/CRITICAL
    - Memory > 80%   → WARNING
    - Error rate > 5% → CRITICAL
    - Connection wait > 5000ms → CRITICAL
- Returns: the raw metrics data + a health status summary

IN THE REAL WORLD:
Instead of reading JSON files, this would connect to:
- Prometheus (metrics database)
- Grafana (metrics dashboard)
- Datadog / New Relic (monitoring platforms)
- AWS CloudWatch Metrics
=============================================================================
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def run_metrics_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Metrics Agent Node:
    Loads telemetry metrics JSON for the target service, checks for resource
    spikes (CPU, memory, database limits), and generates a health summary.
    """
    print("\n[Node: Metrics Agent] Analyzing metrics...")
    service = state.get("service", "orders")
    
    # ---- Step 1: Build path to the metrics JSON file ----
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    metrics_dir = os.path.join(project_dir, "metrics")
    metrics_file = os.path.join(metrics_dir, f"{service}.json")  # e.g., "metrics/orders.json"
    
    metrics_data = {}  # Will store the parsed JSON data
    summary = ""
    
    # ---- Step 2: Read and parse the JSON file ----
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                # json.load() reads a JSON file and converts it to a Python dictionary
                # e.g., {"cpu": 92, "memory": 84} becomes a Python dict
                metrics_data = json.load(f)
            print(f"[MetricsAgent] Loaded metrics for '{service}': {metrics_data}")
        except Exception as e:
            err_msg = f"Error reading metrics JSON file: {e}"
            print(f"[MetricsAgent] {err_msg}")
            summary = err_msg
    else:
        err_msg = f"Metrics file for service '{service}' not found at {metrics_file}"
        print(f"[MetricsAgent] {err_msg}")
        summary = err_msg

    # ---- Step 3: Analyze the metrics (AI or rule-based) ----
    if not summary and metrics_data:
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            try:
                
                # Send the metrics as JSON text to the AI for interpretation
                prompt = f"""
                You are an SRE Metrics Analysis Agent.
                The following system metrics were collected for the '{service}' service:
                
                {json.dumps(metrics_data, indent=2)}
                
                Analyze these metrics and summarize:
                1. What values are abnormally high or low (e.g., resource exhaustion).
                2. Potential implications of these metrics.
                3. Overall status (Healthy, Warning, Critical).
                
                Keep your summary professional and concise.
                """
                from utils.gemini_helper import generate

                summary = generate(prompt).strip()
                
            except Exception as e:
                print(f"[MetricsAgent] Gemini API error: {e}. Falling back to rule-based checks.")
                api_key = None
        
        # ---- Fallback: Simple threshold-based rule engine ----
        if not api_key:
            summary = f"### Telemetry Metrics Summary for '{service}'\n"
            summary += f"Loaded telemetry metrics from `{service}.json`:\n\n"
            
            status = "HEALTHY"     # Start optimistic, downgrade if problems found
            anomalies = []         # List of detected problems
            
            for key, val in metrics_data.items():
                # Skip non-numeric fields like "service" and "timestamp"
                if key in ["service", "timestamp"]:
                    continue
                summary += f"- **{key.replace('_', ' ').title()}**: {val}\n"
                
                # ---- Threshold checks ----
                # These are common SRE "golden signals" thresholds
                if key == "cpu" and val > 80:
                    anomalies.append(f"High CPU utilization: {val}% (threshold 80%)")
                    status = "CRITICAL"
                elif key == "memory" and val > 80:
                    anomalies.append(f"High memory utilization: {val}% (threshold 80%)")
                    if status != "CRITICAL":
                        status = "WARNING"
                elif key == "error_rate" and val > 5:
                    anomalies.append(f"High HTTP error rate: {val}% (threshold 5%)")
                    status = "CRITICAL"
                elif key == "connection_wait_time_ms" and val > 5000:
                    anomalies.append(f"Extreme database connection wait time: {val}ms")
                    status = "CRITICAL"
            
            summary += f"\n**Overall Status**: {status}\n"
            if anomalies:
                summary += "\n**Detected Anomalies**:\n"
                for anomaly in anomalies:
                    summary += f"- ⚠️ {anomaly}\n"
            else:
                summary += "\nNo metrics exceeded critical operational thresholds."

    # ---- Step 4: Return updates to the state ----
    return {
        "metrics_analyzed": metrics_data,  # Raw metrics dictionary
        "metrics_summary": summary,         # Human-readable summary
        "current_step": "metrics"           # Track progress
    }
