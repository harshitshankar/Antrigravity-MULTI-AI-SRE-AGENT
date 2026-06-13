"""
=============================================================================
FILE: agents/planner.py
PURPOSE: The FIRST agent in the pipeline. It reads the user's incident
         description and figures out:
         1. Which service is affected (orders, payment, or inventory)
         2. What investigation steps should be taken (creates a checklist)
=============================================================================

HOW IT WORKS:
- Receives the user's query (e.g., "Orders API returning 500 errors")
- First tries keyword matching to identify the service name
- If GEMINI_API_KEY is set, asks Google Gemini AI to create a smart plan
- If no API key, falls back to a pre-written template plan
- Returns: the identified service name + the investigation plan

WHAT IS A LANGGRAPH NODE?
A "node" is just a regular Python function that:
  1. Takes the current state dictionary as input
  2. Does some work (analysis, API calls, etc.)
  3. Returns a dictionary with ONLY the fields it wants to update
LangGraph automatically merges the returned dict into the main state.
=============================================================================
"""

import os
import re
from typing import Dict, Any
from dotenv import load_dotenv  # Reads .env file to get API keys

# load_dotenv() reads the .env file in your project folder and loads
# any variables (like GEMINI_API_KEY) into the environment so we can
# access them with os.getenv()
load_dotenv()


def run_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planner Agent Node:
    Assesses the incident description, identifies the target service,
    and constructs a structured SRE investigation plan.
    
    This is the ENTRY POINT of the agent pipeline — it runs first.
    """
    print("\n[Node: Planner Agent] Assessing incident query...")
    
    # ---- Step 1: Extract the user's query from the state ----
    query = state.get("query", "")  # .get() is safe — returns "" if key doesn't exist
    
    # ---- Step 2: Simple keyword matching to identify the service ----
    # We check if certain words appear in the query to guess which service is affected.
    # This is a simple rule-based approach that works even without AI.
    service = "unknown"
    query_lower = query.lower()  # Convert to lowercase so "Orders" matches "orders"
    
    if "order" in query_lower:
        service = "orders"
    elif "pay" in query_lower or "stripe" in query_lower or "card" in query_lower:
        service = "payment"
    elif "inventory" in query_lower or "stock" in query_lower or "warehouse" in query_lower:
        service = "inventory"
    
    # ---- Step 3: Try using Google Gemini AI to create a smarter plan ----
    api_key = os.getenv("GEMINI_API_KEY")  # Read API key from environment/.env file
    plan = ""
    
    if api_key:
        try:
            # Import the Google Generative AI library
            # Build the prompt FIRST
            prompt = f"""
            You are the Lead SRE Planner Agent. A production incident was reported:
            "{query}"

            Identify the service targeted by this incident (choose exactly from: 'orders', 'payment', 'inventory', or 'unknown').

            Then create a step-by-step SRE investigation plan.

            Include:
            1. Which log files should be searched.
            2. Which metrics should be inspected.
            3. What KEDB entries are relevant.

            Respond in this format:

            SERVICE: <service_name>

            PLAN:
            - [ ] Step 1...
            - [ ] Step 2...
            """

            from utils.gemini_helper import generate

            response_text = generate(prompt)
            
            # ---- Parse the AI's response to extract the service name ----
            # We use a "regex" (regular expression) to find the pattern "SERVICE: orders"
            match = re.search(r"SERVICE:\s*(\w+)", response_text, re.IGNORECASE)
            if match:
                parsed_service = match.group(1).lower().strip()
                if parsed_service in ["orders", "payment", "inventory"]:
                    service = parsed_service  # Use the AI's answer
                
            # Remove the "SERVICE:" line from the plan text
            plan = re.sub(r"SERVICE:\s*\w+", "", response_text, flags=re.IGNORECASE).strip()
            plan = plan.replace("PLAN:", "").strip()
            
        except Exception as e:
            # If anything goes wrong with the AI (network error, invalid key, etc.),
            # we catch the error and fall back to the template plan below
            print(f"[Planner] Gemini API error: {e}. Falling back to rule-based planner.")
            api_key = None  # This triggers the fallback below
    
    # ---- Step 4: Fallback — create a template plan if AI is unavailable ----
    if not api_key or not plan:
        service_capitalized = service.capitalize() if service != "unknown" else "Affected"
        plan = f"""### SRE Investigation Checklist for {service_capitalized} Service
- [ ] Parse service logs under `logs/{service}.log` looking for ERROR and WARN statements.
- [ ] Load telemetry metrics from `metrics/{service}.json` to evaluate resource pressure.
- [ ] Run a similarity search on KEDB (Known Error Database) documents using terms from the incident report.
- [ ] Evaluate system telemetry anomalies to diagnose the root cause.
- [ ] Propose automated or manual remediation and request human authorization."""

    print(f"[Planner] Identified Service: {service}")
    
    # ---- Step 5: Return the updates to the state ----
    # We only return the fields we want to update. LangGraph merges these
    # into the main state automatically.
    return {
        "service": service,              # Which service we identified
        "investigation_plan": plan,       # The checklist we created
        "current_step": "planner"         # Track that this agent has run
    }
