# 🛡️ Enterprise AI SRE Copilot

> An AI-powered Site Reliability Engineering assistant that automatically investigates production incidents, analyzes logs & metrics, searches knowledge bases, diagnoses root causes, and generates incident reports — all with human-in-the-loop approval.

---

## 📖 Table of Contents

1. [What Does This Project Do?](#-what-does-this-project-do)
2. [How It Works (Architecture)](#-how-it-works-architecture)
3. [Folder Structure Explained](#-folder-structure-explained)
4. [Complete Local Setup Guide](#-complete-local-setup-guide-step-by-step)
5. [Running the Application](#-running-the-application)
6. [Running with Docker (Easy Mode)](#-running-with-docker-easy-mode)
7. [How to Use the Dashboard](#-how-to-use-the-dashboard)
8. [Testing the FastAPI Backend Directly](#-testing-the-fastapi-backend-directly)
9. [Deploying to the Cloud](#-deploying-to-the-cloud)
10. [Connecting Real Data Sources](#-connecting-real-data-sources-replacing-fake-data)
11. [Troubleshooting](#-troubleshooting)

---

## 🤔 What Does This Project Do?

Imagine you're an engineer and your production system breaks at 3 AM. You get an alert:

> "Orders API is returning 500 errors"

Instead of manually checking logs, metrics, and runbooks, this system does it ALL automatically:

```
You type: "Orders API is returning 500 errors"
              ↓
🤖 Planner Agent    → Creates an investigation checklist
📝 Log Agent        → Reads log files, finds errors
📊 Metrics Agent    → Checks CPU, memory, error rates
🔍 KEDB/RAG Agent   → Searches knowledge base for known fixes
🧠 Diagnosis Agent  → Determines the root cause
⚠️ Human Approval   → Asks YOU if the fix should be applied
📄 Report Agent     → Generates a professional incident report
```

**Think of it as**: A mini ServiceNow + Splunk + AI SRE assistant combined into one dashboard.

---

## 🏗️ How It Works (Architecture)

### The Agent Pipeline (LangGraph)

```
                     User types incident description
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  Planner Agent   │  ← Identifies service, creates checklist
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │   Log Agent      │  ← Reads .log files, finds ERROR/WARN lines
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Metrics Agent   │  ← Reads .json metrics, checks thresholds
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  KEDB/RAG Agent  │  ← Searches knowledge base via ChromaDB
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ Diagnosis Agent  │  ← Combines all data → root cause + fix
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ ⚠️ HUMAN APPROVAL │  ← Graph PAUSES here, waits for you
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Report Agent    │  ← Generates markdown incident report
                          └────────┬────────┘
                                   │
                                   ▼
                          📄 Saved to reports/ folder
```

### Tech Stack

| Component | Technology | What It Does |
|-----------|-----------|--------------|
| **AI Brain** | LangGraph | Connects all agents in a pipeline (like a flowchart) |
| **LLM** | Google Gemini API | The AI model that reads/analyzes/writes text |
| **Knowledge Search** | ChromaDB | Vector database that finds similar documents |
| **Backend API** | FastAPI | REST API server (like Express.js but for Python) |
| **Frontend UI** | Streamlit | Beautiful dashboard (no HTML/CSS needed!) |
| **Charts** | Plotly | Interactive bar charts for metrics |
| **Data Models** | Pydantic | Validates data structures |

---

## 📁 Folder Structure Explained

```
enterprise-ai-sre/
│
├── agents/                    # 🤖 ALL the AI agent logic lives here
│   ├── __init__.py            #    Makes this folder a Python "package" (required)
│   ├── state.py               #    Defines the "state" — data shared between agents
│   ├── graph.py               #    Connects all agents into a pipeline using LangGraph
│   ├── planner.py             #    Agent 1: Creates investigation checklist
│   ├── log_agent.py           #    Agent 2: Reads and analyzes log files
│   ├── metrics_agent.py       #    Agent 3: Reads and checks metric thresholds
│   ├── RAG_agent.py           #    Agent 4: Searches knowledge base for fixes
│   ├── diagnosis_agent.py     #    Agent 5: Determines root cause + suggests fix
│   └── report_agent.py        #    Agent 6: Generates final incident report
│
├── rag/                       # 🔍 Vector search / knowledge base logic
│   ├── __init__.py            #    Makes this folder a Python package
│   └── vector_store.py        #    ChromaDB setup + document indexing + search
│
├── kedb/                      # 📚 Known Error Database (markdown articles)
│   ├── db_pool_exhausted.md   #    Runbook: Database connection pool issues
│   ├── payment_gateway_timeout.md  # Runbook: Payment API timeout issues
│   └── rate_limit_exceeded.md #    Runbook: API rate limiting issues
│
├── logs/                      # 📝 Fake production log files (simulated data)
│   ├── orders.log             #    Log events for Orders service
│   ├── inventory.log          #    Log events for Inventory service
│   └── payment.log            #    Log events for Payment service
│
├── metrics/                   # 📊 Fake system metrics (JSON files)
│   ├── orders.json            #    CPU, memory, error rates for Orders service
│   ├── inventory.json         #    CPU, memory, error rates for Inventory service
│   └── payment.json           #    CPU, memory, error rates for Payment service
│
├── reports/                   # 📄 Generated incident reports are saved here
│
├── ui/                        # 🖥️ Frontend dashboard
│   └── app.py                 #    Streamlit dashboard with 5 tabs
│
├── venv/                      # 🐍 Python virtual environment (created during setup)
├── main.py                    # 🚀 FastAPI backend server (API endpoints)
├── test_agents.py             # ✅ Automated test script
├── requirements.txt           # 📦 List of Python packages needed
├── .env.example               # 🔑 Template for API key configuration
└── README.md                  # 📖 This file!
```

---

## 🚀 Complete Local Setup Guide (Step by Step)

### Prerequisites

- **Python 3.10 or higher** installed on your laptop
- **8 GB RAM** minimum (no GPU needed!)
- **Windows / Mac / Linux** — all work

### Step 1: Verify Python is Installed

Open your terminal (Command Prompt / PowerShell on Windows, Terminal on Mac/Linux):

```bash
python --version
```

You should see something like `Python 3.11.x` or `Python 3.12.x`. If not, download Python from [python.org](https://www.python.org/downloads/).

> ⚠️ **Windows Users**: During Python installation, make sure to check the box that says **"Add Python to PATH"**!

### Step 2: Navigate to the Project Folder

```bash
# Windows (PowerShell)
cd C:\Users\ravi3_3e8ym6i\.gemini\antigravity\scratch\enterprise-ai-sre

# OR if you copied the project somewhere else:
cd path\to\enterprise-ai-sre
```

### Step 3: Create a Virtual Environment

A virtual environment is like a separate container for your project's packages so they don't conflict with other Python projects on your computer.

```bash
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv
```

### Step 4: Activate the Virtual Environment

```bash
# Windows (PowerShell)
.\venv\Scripts\activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Mac/Linux
source venv/bin/activate
```

> ✅ You'll see `(venv)` appear at the start of your terminal line — that means it's working!

### Step 5: Install All Required Packages

```bash
pip install -r requirements.txt
```

This downloads and installs everything (Streamlit, FastAPI, LangGraph, ChromaDB, etc.). It may take 2-5 minutes depending on your internet speed.

### Step 6: Set Up Your Gemini API Key (Optional but Recommended)

The app works in two modes:

| Mode | What Happens | API Key Needed? |
|------|-------------|-----------------|
| **Mock Mode** | Uses pre-written rule-based responses | ❌ No |
| **AI Mode** | Uses Google Gemini to dynamically analyze & respond | ✅ Yes |

**To get a free Gemini API key:**

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key (it starts with `AIza...`)

**To configure it:**

1. Create a new file called `.env` in the project root folder (same level as `main.py`)
2. Add this line:

```ini
GEMINI_API_KEY=AIzaSyYOUR_ACTUAL_KEY_HERE
```

> 💡 **Without the API key**, the app still works perfectly using intelligent rule-based fallbacks! Great for demos and learning.

### Step 7: Run the Verification Test

This runs a quick test to make sure everything is installed correctly:

```bash
python test_agents.py
```

You should see output ending with:

```
==================================================
Integration Test Completed Successfully!
==================================================
```

---

## ▶️ Running the Application

You need **TWO terminal windows** running at the same time.

### Terminal 1: Start the FastAPI Backend

```bash
# Make sure you're in the project folder and venv is activated
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Mac/Linux

python main.py
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

> 🌐 Your API is now live at: **http://127.0.0.1:8000**
> 📖 API docs are at: **http://127.0.0.1:8000/docs** (auto-generated Swagger UI!)

### Terminal 2: Start the Streamlit Dashboard

Open a **new** terminal window:

```bash
# Navigate to the project folder
cd C:\Users\ravi3_3e8ym6i\.gemini\antigravity\scratch\enterprise-ai-sre

# Activate venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Mac/Linux

# Start Streamlit
streamlit run ui/app.py
```

You should see:

```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

> 🖥️ Open your browser and go to: **http://localhost:8501**

---

## 🐳 Running with Docker (Easy Mode)

If you don't want to install Python packages on your laptop or deal with environment paths, you can run the entire system inside Docker. 

### ❓ Do I need a Virtual Environment (`venv`) for Docker?
**No!** You do not need to create or activate a virtual environment (`venv`) on your host machine when using Docker. 
* **Why?** Docker builds isolated containers (like mini-Linux systems). All Python libraries are installed inside those containers automatically.
* **When would I need a `venv`?** Only if you decide to run the project natively (without Docker) using the `Complete Local Setup Guide` above.

### Prerequisites for Docker
Make sure you have **Docker Desktop** installed and running on your machine:
- Download it here: [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### How to Run Locally with Docker Compose

We use `docker-compose.yml` to automatically build, run, and link the frontend and backend containers together.

1. **Configure your Gemini API Key** (optional but recommended):
   Create a `.env` file in the project root folder (same folder as `docker-compose.yml`):
   ```ini
   GEMINI_API_KEY=AIzaSyYOUR_KEY_HERE
   ```

2. **Build and start the containers**:
   Open your terminal (PowerShell, Command Prompt, or Terminal) and run:
   ```bash
   docker-compose up --build
   ```

   *This command will download the python base images, copy your code, install all dependencies, and spin up both servers. This might take a few minutes on the first run.*

3. **Access the application**:
   - **Frontend UI (Streamlit)**: Open your browser to **[http://localhost:8501](http://localhost:8501)**
   - **Backend API (FastAPI)**: Access it at **[http://localhost:8000](http://localhost:8000)** (docs at `http://localhost:8000/docs`)

4. **Stop the containers**:
   Press `Ctrl + C` in your terminal, or run:
   ```bash
   docker-compose down
   ```

> 💾 **Data Persistence**: The `docker-compose.yml` file is configured with a volume mount for `./reports:/app/reports`. This means any incident post-mortem reports generated by the AI SRE will be saved directly to your host machine's `reports/` folder, so they won't be lost when containers are deleted!

---

## 🖥️ How to Use the Dashboard

The dashboard has **5 tabs**:

### Tab 1: 📈 Dashboard
- Shows the health status of all 3 services (Orders, Inventory, Payment)
- Displays CPU %, Memory %, Error Rate % for each
- Color-coded badges: 🟢 HEALTHY, 🟡 WARNING, 🔴 CRITICAL
- Shows recent log tails

### Tab 2: 📝 Logs View
- Select a service from the dropdown
- Search/filter logs by keyword (e.g., type "ERROR" to see only error lines)
- Displays the raw log file contents

### Tab 3: 📊 Telemetry
- Bar charts comparing CPU and Memory across all 3 services
- Error rate chart highlighting which services have issues

### Tab 4: 🧠 Investigation Workflow (THE MAIN FEATURE)
1. Type an incident description in the text box, e.g.:
   - `Orders API is returning 500 errors`
   - `Payment checkout failing with gateway timeouts`
   - `Inventory sync warnings: SKU-8841 stock levels critical`
2. Click **"Trigger AI Investigation Workflow"**
3. Watch as each agent runs and reports its findings
4. When it reaches the approval step, click **✅ Approve** or **❌ Reject**
5. The final incident report appears

### Tab 5: 📁 Incident Reports
- Browse all previously generated incident reports
- Select one from the dropdown to view it
- Download as a markdown file

---

## 🧪 Testing the FastAPI Backend Directly

You don't have to use the dashboard — you can call the API directly using your browser or tools like `curl` or Postman.

### Using the Swagger UI (Easiest for beginners!)

1. Open your browser
2. Go to: **http://127.0.0.1:8000/docs**
3. You'll see all available API endpoints with a "Try it out" button

### Using curl (Command Line)

#### 1. Check System Health

```bash
curl http://127.0.0.1:8000/api/system/health
```

This returns the CPU, memory, and error rate for all services.

#### 2. Trigger an Incident Investigation

```bash
curl -X POST http://127.0.0.1:8000/api/incident/trigger ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Orders API is returning 500 errors\"}"
```

> 📌 Note the `incident_id` in the response (e.g., `INC-A1B2C3`). You'll need it for the next steps.

#### 3. Check Incident Status

```bash
curl http://127.0.0.1:8000/api/incident/INC-A1B2C3
```

Replace `INC-A1B2C3` with your actual incident ID.

#### 4. Approve the Remediation

```bash
curl -X POST http://127.0.0.1:8000/api/incident/INC-A1B2C3/approve ^
  -H "Content-Type: application/json" ^
  -d "{\"approved\": true}"
```

#### 5. View Generated Reports

```bash
curl http://127.0.0.1:8000/api/system/reports
```

### Using Python (requests library)

```python
import requests

# Trigger an incident
response = requests.post(
    "http://127.0.0.1:8000/api/incident/trigger",
    json={"query": "Orders API is returning 500 errors"}
)
data = response.json()
incident_id = data["incident_id"]
print(f"Incident ID: {incident_id}")

# Approve the remediation
response = requests.post(
    f"http://127.0.0.1:8000/api/incident/{incident_id}/approve",
    json={"approved": True}
)
report = response.json()["state"]["final_report"]
print(report)
```

---

## ☁️ Deploying to the Cloud

### Option 1: Deploy on Render (Recommended — Free Tier Available)

[Render](https://render.com) is the easiest platform for deploying Python apps.

#### Step A: Prepare for Deployment

1. **Create a `render.yaml`** file in your project root:

```yaml
services:
  # FastAPI Backend
  - type: web
    name: sre-copilot-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false    # You'll set this manually in Render dashboard

  # Streamlit Frontend
  - type: web
    name: sre-copilot-ui
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run ui/app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: API_BASE_URL
        value: https://sre-copilot-api.onrender.com
      - key: GEMINI_API_KEY
        sync: false
```

2. **Push your code to GitHub:**

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit: Enterprise AI SRE Copilot"

# Create a repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/enterprise-ai-sre.git
git push -u origin main
```

3. **Add a `.gitignore`** file to avoid uploading unnecessary files:

```
venv/
__pycache__/
*.pyc
.env
rag/chroma_db/
reports/*.md
```

#### Step B: Deploy on Render

1. Go to [render.com](https://render.com) and sign up (free)
2. Click **"New" → "Blueprint"**
3. Connect your GitHub repo
4. Render will auto-detect the `render.yaml` and create both services
5. Go to each service's **Environment** tab and add your `GEMINI_API_KEY`
6. Wait for the build to complete (3-5 minutes)

> 🌐 Your app will be live at: `https://sre-copilot-ui.onrender.com`

#### Step C: Update the Frontend API URL

In `ui/app.py`, the frontend connects to the backend. Update the `API_BASE_URL` environment variable in Render to point to your deployed backend URL.

---

### Option 2: Deploy on Railway (Easy, Free Tier)

[Railway](https://railway.app) is another great option:

1. Sign up at [railway.app](https://railway.app)
2. Click **"New Project" → "Deploy from GitHub"**
3. Select your repo
4. Add a **Procfile** to your project root:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

5. For the Streamlit frontend, create a second Railway service with:

```
web: streamlit run ui/app.py --server.port $PORT --server.address 0.0.0.0
```

6. Set `GEMINI_API_KEY` and `API_BASE_URL` in Railway's environment variables

---

### Option 3: Deploy on Vercel (Frontend Only)

> ⚠️ Vercel is optimized for JavaScript/Next.js apps. It **cannot** run Streamlit or FastAPI natively. However, you can deploy the FastAPI backend as a **Serverless Function**.

For a Python project like this, **Render or Railway are much better choices** than Vercel.

If you specifically want Vercel:
1. Deploy the **FastAPI backend** on Render/Railway
2. Build a separate **Next.js or React frontend** that calls the FastAPI endpoints
3. Deploy that frontend on Vercel

---

### Option 4: Deploying as a Docker Container in the Cloud

Deploying with Docker ensures that your cloud environment exactly matches your local laptop, eliminating "it works on my machine" issues.

#### 1. Deploying on Render (via Docker)
Render can automatically build and run services using Dockerfiles.
1. Create two separate Web Services on Render.
2. **Backend Web Service**:
   - Runtime: Select **Docker** (Render will automatically detect your `Dockerfile.backend` if you specify it).
   - In **Advanced Settings**, set the Dockerfile Path to `Dockerfile.backend`.
   - Add environment variable `GEMINI_API_KEY`.
3. **Frontend Web Service**:
   - Runtime: Select **Docker**.
   - In **Advanced Settings**, set the Dockerfile Path to `Dockerfile.frontend`.
   - Add environment variable `API_BASE_URL` pointing to the backend's Render URL (e.g. `https://sre-copilot-api.onrender.com`).
   - Add environment variable `GEMINI_API_KEY`.

#### 2. Deploying on Google Cloud Run (Serverless Docker)
Google Cloud Run is highly optimized for containerized apps and has a very generous free tier.
1. Install the Google Cloud SDK and log in:
   ```bash
   gcloud auth login
   ```
2. Build and push your backend image to Google Artifact Registry:
   ```bash
   # Build the backend image
   docker build -t gcr.io/YOUR_PROJECT_ID/sre-backend -f Dockerfile.backend .
   # Push to GCP Registry
   docker push gcr.io/YOUR_PROJECT_ID/sre-backend
   ```
3. Deploy the backend to Cloud Run:
   ```bash
   gcloud run deploy sre-backend --image gcr.io/YOUR_PROJECT_ID/sre-backend --platform managed --allow-unauthenticated --set-env-vars="GEMINI_API_KEY=your_key"
   ```
   *(Note down the service URL returned by this command).*
4. Build and push the frontend image:
   ```bash
   # Build the frontend image
   docker build -t gcr.io/YOUR_PROJECT_ID/sre-frontend -f Dockerfile.frontend .
   # Push to GCP Registry
   docker push gcr.io/YOUR_PROJECT_ID/sre-frontend
   ```
5. Deploy the frontend to Cloud Run:
   ```bash
   gcloud run deploy sre-frontend --image gcr.io/YOUR_PROJECT_ID/sre-frontend --platform managed --allow-unauthenticated --set-env-vars="API_BASE_URL=https://sre-backend-xxx.run.app,GEMINI_API_KEY=your_key"
   ```

#### 3. Deploying on Railway (via Docker)
Railway automatically detects Dockerfiles!
1. If you push a repository with `Dockerfile.backend` and `Dockerfile.frontend` to GitHub, Railway will let you choose which service to build.
2. Select your repository in Railway.
3. In the service settings under **Build**, specify the path to the Dockerfile (e.g., `Dockerfile.backend` for the backend, `Dockerfile.frontend` for the frontend).
4. Configure variables `API_BASE_URL` and `GEMINI_API_KEY` in Railway's **Variables** tab.

---

## 🔌 Connecting Real Data Sources (Replacing Fake Data)

Right now, the app reads fake log files and JSON metrics. Here's how to swap each one for real production systems:

### 1. Replace Fake Logs with Splunk

**Current behavior**: The Log Agent reads `.log` files from the `logs/` folder.

**To connect to Splunk:**

Edit `agents/log_agent.py` — replace the file-reading section with Splunk API calls:

```python
# ---- BEFORE (fake logs) ----
log_file = os.path.join(logs_dir, f"{service}.log")
with open(log_file, "r") as f:
    lines = f.readlines()

# ---- AFTER (real Splunk integration) ----
import requests

SPLUNK_HOST = "https://your-splunk-server:8089"
SPLUNK_TOKEN = os.getenv("SPLUNK_TOKEN")  # Add to .env file

def search_splunk(query: str):
    """Search Splunk for log events."""
    headers = {"Authorization": f"Bearer {SPLUNK_TOKEN}"}
    search_query = f'search index=production source="{service}" (ERROR OR WARN) | head 50'
    
    # Create a search job
    response = requests.post(
        f"{SPLUNK_HOST}/services/search/jobs",
        headers=headers,
        data={"search": search_query, "output_mode": "json"},
        verify=False  # Set to True in production with proper SSL
    )
    job_id = response.json()["sid"]
    
    # Get results (wait for job to complete)
    import time
    time.sleep(5)  # Simple wait; use polling in production
    
    results = requests.get(
        f"{SPLUNK_HOST}/services/search/jobs/{job_id}/results",
        headers=headers,
        params={"output_mode": "json"},
        verify=False
    )
    return results.json()["results"]

# Use it:
log_lines = [event["_raw"] for event in search_splunk(service)]
```

**Add to `.env`:**
```ini
SPLUNK_HOST=https://your-splunk-server:8089
SPLUNK_TOKEN=your_splunk_api_token
```

---

### 2. Replace Fake Metrics with Prometheus/Grafana

**Current behavior**: The Metrics Agent reads `.json` files from the `metrics/` folder.

**To connect to Prometheus:**

Edit `agents/metrics_agent.py`:

```python
# ---- BEFORE (fake metrics) ----
with open(metrics_file, "r") as f:
    metrics_data = json.load(f)

# ---- AFTER (real Prometheus integration) ----
import requests

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

def query_prometheus(metric_name: str, service: str):
    """Query Prometheus for a specific metric."""
    query = f'{metric_name}{{service="{service}"}}'
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query}
    )
    data = response.json()
    if data["status"] == "success" and data["data"]["result"]:
        return float(data["data"]["result"][0]["value"][1])
    return 0

# Use it:
metrics_data = {
    "service": service,
    "cpu": query_prometheus("process_cpu_usage", service),
    "memory": query_prometheus("process_memory_usage_bytes", service),
    "error_rate": query_prometheus("http_server_errors_total", service),
}
```

**To connect to Grafana:**

```python
GRAFANA_URL = os.getenv("GRAFANA_URL")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")

def query_grafana_dashboard(dashboard_uid: str):
    headers = {"Authorization": f"Bearer {GRAFANA_API_KEY}"}
    response = requests.get(
        f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}",
        headers=headers
    )
    return response.json()
```

---

### 3. Replace Fake KEDB with ServiceNow

**Current behavior**: The RAG Agent searches markdown files in the `kedb/` folder.

**To connect to ServiceNow Knowledge Base:**

Edit `rag/vector_store.py` — add a method to fetch articles from ServiceNow:

```python
# ---- AFTER (real ServiceNow integration) ----
import requests

SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")  # e.g., "dev12345"
SERVICENOW_USER = os.getenv("SERVICENOW_USER")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD")

def fetch_servicenow_knowledge_articles():
    """Fetch known error articles from ServiceNow."""
    url = f"https://{SERVICENOW_INSTANCE}.service-now.com/api/now/table/kb_knowledge"
    auth = (SERVICENOW_USER, SERVICENOW_PASSWORD)
    params = {
        "sysparm_query": "workflow_state=published",
        "sysparm_fields": "short_description,text,number",
        "sysparm_limit": 100
    }
    response = requests.get(url, auth=auth, params=params)
    articles = response.json()["result"]
    
    documents = []
    for article in articles:
        documents.append({
            "id": article["number"],
            "title": article["short_description"],
            "content": article["text"],
            "path": f"servicenow://{article['number']}"
        })
    return documents
```

Then, in the `KEDBIndex.__init__` method, call `fetch_servicenow_knowledge_articles()` instead of loading from local markdown files.

---

### 4. Connect to Kubernetes for Pod Metrics

**To get real Kubernetes pod metrics:**

```python
# pip install kubernetes
from kubernetes import client, config

def get_kubernetes_pod_status(namespace: str, service: str):
    """Get pod status from a Kubernetes cluster."""
    # Load kubeconfig (works if kubectl is configured on your machine)
    config.load_kube_config()
    # OR for in-cluster: config.load_incluster_config()
    
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(
        namespace=namespace,
        label_selector=f"app={service}"
    )
    
    pod_info = []
    for pod in pods.items:
        pod_info.append({
            "name": pod.metadata.name,
            "status": pod.status.phase,
            "restarts": sum(
                cs.restart_count for cs in (pod.status.container_statuses or [])
            ),
        })
    return pod_info
```

---

### 5. Connect to PagerDuty / Opsgenie for Alerts

```python
# pip install pdpyras  (for PagerDuty)
import os
import requests

PAGERDUTY_API_KEY = os.getenv("PAGERDUTY_API_KEY")

def get_open_incidents():
    """Fetch open incidents from PagerDuty."""
    headers = {
        "Authorization": f"Token token={PAGERDUTY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(
        "https://api.pagerduty.com/incidents",
        headers=headers,
        params={"statuses[]": ["triggered", "acknowledged"]}
    )
    return response.json()["incidents"]
```

---

### 6. Connect to ServiceNow & BMC Helix (ITSM & Ticketing)

Connecting to enterprise ITSM systems lets you automate incident response workflows end-to-end. You can poll for tickets, update work notes, request approvals, and resolve incidents.

#### A. Fetching ServiceNow Tickets (Auto-Trigger SRE Pipeline)

You can run a background job in FastAPI (`main.py`) that polls ServiceNow for newly created critical incidents:

```python
import os
import requests

SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")
SERVICENOW_USER = os.getenv("SERVICENOW_USER")
SERVICENOW_PASS = os.getenv("SERVICENOW_PASSWORD")

def fetch_new_servicenow_incidents():
    """Fetch active, unassigned P1/P2 incidents from ServiceNow."""
    url = f"https://{SERVICENOW_INSTANCE}.service-now.com/api/now/table/incident"
    params = {
        "sysparm_query": "active=true^priorityIN1,2^assigned_toISNULL^state=1",
        "sysparm_fields": "number,short_description,sys_id,description",
        "sysparm_limit": 5
    }
    response = requests.get(
        url, 
        auth=(SERVICENOW_USER, SERVICENOW_PASS), 
        params=params,
        headers={"Accept": "application/json"}
    )
    return response.json().get("result", []) if response.status_code == 200 else []
```

#### B. Posting Investigation Diagnosis & Work Notes

Update the incident's internal SRE logs as the agents compile diagnostics:

```python
def add_work_note_to_incident(incident_sys_id: str, note_text: str):
    """Add a work note update to a ServiceNow incident ticket."""
    url = f"https://{SERVICENOW_INSTANCE}.service-now.com/api/now/table/incident/{incident_sys_id}"
    payload = {
        "work_notes": f"[AI SRE Copilot] {note_text}"
    }
    response = requests.put(
        url,
        auth=(SERVICENOW_USER, SERVICENOW_PASS),
        json=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    return response.status_code == 200
```

#### C. Resolving the Ticket & Syncing Approvals

After the operator approves the remediation action and the pipeline runs it, resolve the ticket automatically:

```python
def resolve_servicenow_incident(incident_sys_id: str, resolution_notes: str):
    """Set incident state to Resolved (state code '6')."""
    url = f"https://{SERVICENOW_INSTANCE}.service-now.com/api/now/table/incident/{incident_sys_id}"
    payload = {
        "state": "6", # '6' is the ServiceNow code for Resolved
        "close_code": "Solved (Workaround)",
        "close_notes": f"Resolved automatically by AI SRE Copilot:\n{resolution_notes}"
    }
    response = requests.put(
        url,
        auth=(SERVICENOW_USER, SERVICENOW_PASS),
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    return response.status_code == 200
```

#### D. Integrating with BMC Helix ITSM

For **BMC Helix**, authenticate using OAuth tokens (`/jwt/login`), and interact with the incident business interfaces:

```python
def helix_login(host, username, password):
    url = f"https://{host}/api/jwt/login"
    response = requests.post(url, data={"username": username, "password": password})
    return response.text  # Returns JWT token string

def update_helix_incident(host, token, incident_id, work_note):
    url = f"https://{host}/api/rx/application/incident/incident/{incident_id}"
    headers = {"Authorization": f"AR-JWT {token}", "Content-Type": "application/json"}
    payload = {
        "workNote": f"[AI SRE Copilot] {work_note}"
    }
    requests.put(url, headers=headers, json=payload)
```

---

### Summary: Environment Variables for Real Integrations

When you connect real sources, your `.env` file will look like:

```ini
# AI Model
GEMINI_API_KEY=AIzaSy...

# Splunk
SPLUNK_HOST=https://splunk.yourcompany.com:8089
SPLUNK_TOKEN=your_token

# Prometheus
PROMETHEUS_URL=http://prometheus.yourcompany.com:9090

# Grafana
GRAFANA_URL=https://grafana.yourcompany.com
GRAFANA_API_KEY=your_grafana_key

# ServiceNow
SERVICENOW_INSTANCE=dev12345
SERVICENOW_USER=admin
SERVICENOW_PASSWORD=your_password

# Kubernetes
KUBE_CONFIG_PATH=~/.kube/config

# PagerDuty
PAGERDUTY_API_KEY=your_pd_key
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'langgraph'"
→ You forgot to activate the virtual environment. Run:
```bash
.\venv\Scripts\activate    # Windows
source venv/bin/activate   # Mac/Linux
```

### "Backend API Offline" message in Streamlit
→ The FastAPI server isn't running. Open a separate terminal and run:
```bash
python main.py
```

### "GEMINI_API_KEY not found" warning
→ This is OK! The app works without it using mock/rule-based responses. To use real AI, add your key to the `.env` file.

### Port already in use
→ Another process is using port 8000 or 8501. Either kill that process or change the port:
```bash
# FastAPI on a different port
uvicorn main:app --port 8001

# Streamlit on a different port
streamlit run ui/app.py --server.port 8502
```

### ChromaDB errors on startup
→ Delete the `rag/chroma_db/` folder and restart. It will be recreated automatically:
```bash
# Windows
rmdir /s /q rag\chroma_db

# Mac/Linux
rm -rf rag/chroma_db
```

### pip install fails with "Permission denied"
→ Make sure you're using a virtual environment (see Step 3 & 4 in setup guide).

---

## 📚 Key Concepts for Beginners

| Term | What It Means |
|------|--------------|
| **SRE** | Site Reliability Engineering — keeping production systems healthy |
| **LangGraph** | A Python library that chains AI agents together like a flowchart |
| **FastAPI** | A Python web framework for building REST APIs (like Express.js) |
| **Streamlit** | A Python library that creates web dashboards with just Python code |
| **ChromaDB** | A vector database that finds "similar" documents using math (embeddings) |
| **Embeddings** | Converting text into numbers so computers can compare similarity |
| **RAG** | Retrieval Augmented Generation — finding relevant docs before asking AI |
| **KEDB** | Known Error Database — a library of past problems and their fixes |
| **Gemini API** | Google's AI model that can read, understand, and generate text |
| **Virtual Environment** | An isolated Python environment for your project's packages |
| **Incident Report** | A formal document describing what broke, why, and how it was fixed |

---

## 🤝 Contributing

This project is designed for learning! Feel free to:
- Add more KEDB articles in the `kedb/` folder
- Add more log files for new services
- Modify agent logic in the `agents/` folder
- Improve the Streamlit UI in `ui/app.py`

---

**Built with ❤️ using Python, LangGraph, FastAPI, Streamlit, ChromaDB, and Google Gemini**

Yes, you can absolutely add and link as many services as you want (e.g. adding a new shipping or auth service).

Here is the step-by-step guide on how to add a new service named shipping:

Step 1: Tell the Backend about the New Service
Open 
main.py
 and add your service name to the services list:

python


# Before
services = ["orders", "inventory", "payment"]
# After
services = ["orders", "inventory", "payment", "shipping"]
Step 2: Create Logs and Metrics Files
The SRE agents need metrics and logs for this service, otherwise, it will complain about missing files.

Create metrics file 
metrics/shipping.json
:
json


{
  "service": "shipping",
  "cpu": 45,
  "memory": 60,
  "error_rate": 0.5,
  "active_deliveries": 320,
  "timestamp": "2026-06-13T14:00:00Z"
}
Create log file 
logs/shipping.log
:
text


2026-06-13T13:58:10Z INFO Shipping service started.
2026-06-13T13:59:00Z INFO Fetching address coordinates for label printing.
2026-06-13T14:00:00Z ERROR FedEx API failure: DNS resolution timed out on api.fedex.com
Step 3: Teach the Planner Agent to Detect the Service
Open 
agents/planner.py
:

Update keyword matching (Line 56):
python


if "order" in query_lower:
    service = "orders"
elif "pay" in query_lower or "stripe" in query_lower or "card" in query_lower:
    service = "payment"
elif "inventory" in query_lower or "stock" in query_lower or "warehouse" in query_lower:
    service = "inventory"
elif "ship" in query_lower or "fedex" in query_lower or "delivery" in query_lower:
    service = "shipping"
Update the LLM instruction prompt list (Line 84): Change: choose exactly from: 'orders', 'payment', 'inventory', or 'unknown' To: choose exactly from: 'orders', 'payment', 'inventory', 'shipping', or 'unknown'
Step 4: Add Fallback Rules to the Diagnosis Agent
If you are running the system without a Gemini API Key, the system needs to know what mock diagnosis to return for shipping. Open 
agents/diagnosis_agent.py
 and add:

python


elif service == "shipping":
    diagnosis = "FedEx API connectivity failure. DNS resolution to api.fedex.com timed out, preventing label generation and dispatch tracking."
    remediation = """1. **Verify Vendor Status**: Check status.fedex.com for API availability.
2. **Switch Carrier**: Route shipments temporarily to backup DHL/UPS carrier endpoints.
3. **Queue Labels**: Store unsent print jobs in local Kafka retry queues and process later."""
Step 5: Add Known Runbooks (Optional for RAG)
Create a new Markdown runbook in the KEDB folder, such as 
kedb/shipping_carrier_failure.md
:

markdown


# Shipping Carrier API Timeout
## Problem
API integration calls to external carriers (FedEx, UPS) time out or fail to resolve.
## Solutions
1. Route shipments through alternative providers.
2. Queue requests locally and retry when carrier returns online.
The RAG Agent will search and load this runbook automatically if the user mentions carrier errors in the incident trigger prompt!

How the Frontend Handles This
Since I just modified 
ui/app.py
, the frontend dashboard will automatically detect the new shipping service from the backend's API response, create a 4th health card on the home screen, populate its performance graphs, and add it to the logs dropdown menu without needing any manual code updates in the UI!


