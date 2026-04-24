# 📋 MCP_IRROPS_Lab — Student Setup Guide

> **Follow every step in order. Do not skip steps.**
> Estimated time: **30–45 minutes** for first-time setup.

---

## 📦 What You Will Set Up

By the end of this guide you will have 4 terminals running simultaneously in VS Code:

```
Terminal 1 → Anomaly Detector    http://localhost:8080
Terminal 2 → Resolution Agent    http://localhost:8081
Terminal 3 → Audit Service       http://localhost:8082
Terminal 4 → React UI            http://localhost:3000
```

All backed by **Vertex AI Gemini 2.5 Pro**, **BigQuery**, and the **MCP Protocol**.

---

## ✅ Prerequisites — Install These First

Install all tools before starting. **After each install, restart VS Code.**

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.11+ | https://python.org/downloads |
| **Node.js** | 18 LTS+ | https://nodejs.org |
| **Google Cloud CLI** | Latest | https://cloud.google.com/sdk/docs/install |
| **VS Code** | Latest | https://code.visualstudio.com |
| **Git** | Latest | https://git-scm.com/download/win (Windows only) |

> ⚠️ When installing Python: check **"Add Python to PATH"**
> When installing Node.js: check **"Add to PATH"**
> When installing Google Cloud CLI on Windows: download the `.exe` installer

### Verify all tools are installed

Open a terminal and run each command. All must print a version number:

```bash
python --version
node --version
npm --version
gcloud --version
git --version
```

> If any command says "not recognized" — restart VS Code and try again.
> If still not working — reinstall that tool and make sure the PATH option is checked.

---

## Part 1 — Get the Code

### Step 1.1 — Clone the repository

Open VS Code. Open a terminal: **Terminal → New Terminal** (or `Ctrl+\``)

```bash
git clone https://github.com/YOUR_INSTRUCTOR_USERNAME/MCP_IRROPS_Lab.git
```

Then navigate into the project folder:

```bash
cd MCP_IRROPS_Lab
```

> ⚠️ **Windows users — critical path warning:**
> Your project folder path must NOT contain special characters like `#`, `&`, or `%`.
>
> ✅ Safe: `C:\Users\John\Desktop\MCP_IRROPS_Lab`
> ❌ Unsafe: `C:\Users\John\Desktop\AIB#5_labs\MCP_IRROPS_Lab`
>
> If your path has special characters, move the project to a safe location before continuing.

### Step 1.2 — Open the project in VS Code

```bash
code .
```

This reopens VS Code with the project folder loaded. You will see the project files in the Explorer panel on the left.

### Step 1.3 — Install VS Code extensions

Press `Ctrl+Shift+X` to open Extensions. Search and install:
- **Python** by Microsoft
- **Pylance** by Microsoft
- **Cloud Code** by Google
- **ES7+ React/Redux** snippets

---

## Part 2 — Python Virtual Environment

> **What is a virtual environment?**
> It is an isolated Python workspace just for this project.
> It prevents package conflicts with other Python projects on your machine.

### Step 2.1 — Confirm you are in the project root

Your terminal prompt must end with `MCP_IRROPS_Lab`. If not:

```bash
cd MCP_IRROPS_Lab
```

### Step 2.2 — Create the virtual environment

**Windows:**
```powershell
python -m venv .venv
```

**Mac/Linux:**
```bash
python3 -m venv .venv
```

A `.venv` folder will appear in the Explorer panel. This is correct.

### Step 2.3 — Activate the virtual environment

**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

> ✅ **How to confirm it worked:**
> Your terminal prompt will now start with `(.venv)`:
> ```
> (.venv) PS C:\Users\John\Desktop\MCP_IRROPS_Lab>
> ```
> **If you do NOT see `(.venv)` — stop and fix this before continuing.**

> ⚠️ **Windows error: "running scripts is disabled"?**
> Run this first, then activate again:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 2.4 — Tell VS Code to always use this venv

1. Press `Ctrl+Shift+P`
2. Type `Python: Select Interpreter` and press Enter
3. Select the option that contains `.venv`:
   - Windows: `.\.venv\Scripts\python.exe`
   - Mac/Linux: `./.venv/bin/python`

After this, every new terminal you open in VS Code will auto-activate the venv.

### Step 2.5 — Verify the venv is active

**Windows:**
```powershell
where python
```
Must show: `C:\...\MCP_IRROPS_Lab\.venv\Scripts\python.exe`

**Mac/Linux:**
```bash
which python3
```
Must show: `/path/to/MCP_IRROPS_Lab/.venv/bin/python3`

---

## Part 3 — Google Cloud Setup

### Step 3.1 — Verify gcloud is working

```bash
gcloud --version
```

Expected output (version numbers may differ):
```
Google Cloud SDK 470.0.0
bq 2.1.0
core 2024.01.01
```

If you get "not found" — install from https://cloud.google.com/sdk/docs/install, then restart VS Code.

### Step 3.2 — Create a new GCP configuration

A configuration is a saved profile for one GCP account. We create a new one so this lab stays separate from any other GCP accounts.

```bash
gcloud init
```

Follow these choices exactly:

**Prompt 1:**
```
Pick configuration to use:
 [1] Re-initialize this configuration [default]...
 [2] Create a new configuration
```
→ Type `2` and press Enter

**Prompt 2:**
```
Enter configuration name:
```
→ Type `MCP-IRROPS-Lab` and press Enter

**Prompt 3:**
```
Choose account to use:
 [1] your-existing@email.com
 [2] Log in with a new account
```
→ Select your Google account (or log in with a new one — browser will open)

**Prompt 4:**
```
Pick cloud project to use:
 [1] existing-project
 [2] Create a new project
```
→ Select your GCP project or create a new one

**Prompt 5:**
```
Do you want to configure a default Compute Region and Zone?
```
→ Type `Y` and press Enter

**Prompt 6 — zone selection:**
→ Type `9` to choose `us-central1-a`, or search the list for us-central1-a

### Step 3.3 — Confirm your configuration is correct

```bash
gcloud config list
```

You must see your email and project ID:
```
[core]
account = your-email@gmail.com
project = your-project-id
```

If project shows `(unset)`:
```bash
gcloud config set project YOUR_PROJECT_ID
```

### Step 3.4 — Set Application Default Credentials

> **This is the most important step in the entire setup.**
> ADC (Application Default Credentials) is what allows your Python code
> to authenticate with Vertex AI, BigQuery, and other GCP services.
> Without this, all services will run in demo mode only.

**Windows PowerShell** — copy and paste this as one single line:
```powershell
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform --no-launch-browser
```

**Mac/Linux:**
```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --no-launch-browser
```

The terminal will print a long URL. Copy it → paste into your browser → sign in with Google → copy the verification code the browser shows → paste it back into the terminal.

✅ You must see:
```
Credentials saved to file: [.../application_default_credentials.json]
Quota project "your-project-id" was added to ADC
```

> ⚠️ **Getting "Access blocked: Authorization Error"?**
> Try this alternative:
> ```bash
> gcloud auth login --no-launch-browser
> gcloud auth application-default set-quota-project YOUR_PROJECT_ID
> ```

### Step 3.5 — Enable required GCP APIs

First save your project ID into a variable.

**Windows PowerShell:**
```powershell
$PROJECT_ID = $(gcloud config get-value project)
echo $PROJECT_ID
```

**Mac/Linux:**
```bash
export PROJECT_ID=$(gcloud config get-value project)
echo $PROJECT_ID
```

Confirm it prints your actual project ID. Then enable the APIs:

```bash
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
gcloud services enable pubsub.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
```

Each prints: `Operation "operations/..." finished successfully.`

### Step 3.6 — Set environment variables

These tell the Python services which project and model to use. Run in every terminal before starting a service.

**Windows PowerShell:**
```powershell
$env:GCP_PROJECT_ID = $(gcloud config get-value project)
$env:GCP_LOCATION = "us-central1"
$env:GEMINI_MODEL = "gemini-2.5-pro"
```

**Mac/Linux:**
```bash
export GCP_PROJECT_ID=$(gcloud config get-value project)
export GCP_LOCATION="us-central1"
export GEMINI_MODEL="gemini-2.5-pro"
```

> 💡 **Make permanent on Mac/Linux:** Add the three export lines to `~/.bashrc` or `~/.zshrc`

---

## Part 4 — BigQuery Setup

> **Why BigQuery?**
> The Anomaly Detector fetches live flight data from BigQuery instead of hardcoded data.
> This makes the demo behave like a real system. You can update values in the BigQuery
> Console and watch anomalies appear in real time in the UI.

### Step 4.1 — Create the dataset

```bash
bq --project_id=$PROJECT_ID mk --dataset --location=US irrops_audit
```

Expected: `Dataset 'your-project-id:irrops_audit' successfully created.`

### Step 4.2 — Create the audit_log table

**Windows PowerShell** (one single line):
```powershell
bq --project_id=$PROJECT_ID mk --table irrops_audit.audit_log action_id:STRING,event_id:STRING,flight:STRING,agent:STRING,tool_called:STRING,proposed_action:STRING,confidence:FLOAT,status:STRING,approved_by:STRING,regulatory_impact:BOOLEAN,assessed_at:TIMESTAMP,escalated_at:TIMESTAMP,notes:STRING
```

**Mac/Linux:**
```bash
bq --project_id=$PROJECT_ID mk --table irrops_audit.audit_log \
  action_id:STRING,event_id:STRING,flight:STRING,agent:STRING,\
  tool_called:STRING,proposed_action:STRING,confidence:FLOAT,\
  status:STRING,approved_by:STRING,regulatory_impact:BOOLEAN,\
  assessed_at:TIMESTAMP,escalated_at:TIMESTAMP,notes:STRING
```

### Step 4.3 — Create the flight_streams table

**Windows PowerShell** (one single line):
```powershell
bq --project_id=$PROJECT_ID mk --table irrops_audit.flight_streams flight:STRING,route:STRING,delay_min:INTEGER,crew_status:STRING,weather:STRING,updated_at:TIMESTAMP
```

**Mac/Linux:**
```bash
bq --project_id=$PROJECT_ID mk --table irrops_audit.flight_streams \
  flight:STRING,route:STRING,delay_min:INTEGER,\
  crew_status:STRING,weather:STRING,updated_at:TIMESTAMP
```

### Step 4.4 — Seed initial flight data

**Windows PowerShell** (one single line):
```powershell
bq --project_id=$PROJECT_ID query --use_legacy_sql=false "INSERT INTO irrops_audit.flight_streams VALUES ('AA-301','JFK-LAX',0,'OK','CLEAR',CURRENT_TIMESTAMP()), ('UA-445','ORD-MIA',165,'SICK','CLEAR',CURRENT_TIMESTAMP()), ('DL-892','DFW-SEA',0,'OK','STORM',CURRENT_TIMESTAMP()), ('SW-1201','ATL-BOS',0,'NO_SHOW','CLEAR',CURRENT_TIMESTAMP()), ('BA-178','LHR-JFK',45,'OK','WIND',CURRENT_TIMESTAMP()), ('LH-454','FRA-ORD',90,'OK','FOG',CURRENT_TIMESTAMP()), ('AA-999','ORD-JFK',180,'SICK','STORM',CURRENT_TIMESTAMP()), ('DL-777','ATL-LAX',200,'NO_SHOW','STORM',CURRENT_TIMESTAMP()), ('UA-555','DEN-ORD',120,'SICK','FOG',CURRENT_TIMESTAMP()), ('EK-201','DXB-LHR',0,'OK','CLEAR',CURRENT_TIMESTAMP())"
```

**Mac/Linux:**
```bash
bq --project_id=$PROJECT_ID query --use_legacy_sql=false \
'INSERT INTO irrops_audit.flight_streams VALUES
  ("AA-301","JFK-LAX",0,"OK","CLEAR",CURRENT_TIMESTAMP()),
  ("UA-445","ORD-MIA",165,"SICK","CLEAR",CURRENT_TIMESTAMP()),
  ("DL-892","DFW-SEA",0,"OK","STORM",CURRENT_TIMESTAMP()),
  ("SW-1201","ATL-BOS",0,"NO_SHOW","CLEAR",CURRENT_TIMESTAMP()),
  ("BA-178","LHR-JFK",45,"OK","WIND",CURRENT_TIMESTAMP()),
  ("LH-454","FRA-ORD",90,"OK","FOG",CURRENT_TIMESTAMP()),
  ("AA-999","ORD-JFK",180,"SICK","STORM",CURRENT_TIMESTAMP()),
  ("DL-777","ATL-LAX",200,"NO_SHOW","STORM",CURRENT_TIMESTAMP()),
  ("UA-555","DEN-ORD",120,"SICK","FOG",CURRENT_TIMESTAMP()),
  ("EK-201","DXB-LHR",0,"OK","CLEAR",CURRENT_TIMESTAMP())'
```

### Step 4.5 — Confirm tables exist and data was inserted

```bash
bq --project_id=$PROJECT_ID ls irrops_audit
```

Expected:
```
   tableId         Type
 ─────────────────────
  audit_log        TABLE
  flight_streams   TABLE
```

Confirm data:
```bash
bq --project_id=$PROJECT_ID query --use_legacy_sql=false "SELECT flight, delay_min, crew_status, weather FROM irrops_audit.flight_streams"
```

You must see 10 rows of flight data.

---

## Part 5 — Install Python Dependencies

You need **3 separate terminals** in VS Code — one per service.

**To open multiple terminals:** Click the `+` icon in the terminal panel header 3 times.

> ✅ Before running pip install in each terminal, confirm `(.venv)` is visible in the prompt.
> If not, activate it:
> ```powershell
> .venv\Scripts\Activate.ps1    # Windows
> source .venv/bin/activate      # Mac/Linux
> ```



### Terminal 1 — Anomaly Detector

```bash
cd services/anomaly-detector
pip install -r requirements.txt
```

Takes 2–3 minutes. Wait for it to finish completely.

## NOT NEEDED FROM OTHER FOLDERS as they all set installed in the same .venv 
### Terminal 2 — Resolution Agent

```bash
cd services/resolution-agent
pip install -r requirements.txt
```

### Terminal 3 — Audit Service

```bash
cd services/audit-service
pip install -r requirements.txt
```

> 💡 `pip install -r requirements.txt` is a one-time setup step. You do not need to run it again unless `requirements.txt` changes.

---

## Part 6 — Start All Services

### Step 6.1 — Set environment variables in each terminal

Run this in **all 3 service terminals** before starting any service.
Replace `your-project-id` with your actual project ID.

**Windows PowerShell:**
```powershell
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_LOCATION = "us-central1"
$env:GEMINI_MODEL = "gemini-2.5-pro"
```

**Mac/Linux:**
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"
export GEMINI_MODEL="gemini-2.5-pro"
```

### Step 6.2 — Start Anomaly Detector (Terminal 1)

Confirm you are in `services/anomaly-detector`, then:

```bash
python main.py
```

Wait until you see this — do not move on until it appears:
```
════════════════════════════════════════════════════
  IRROPS Anomaly Detector — Starting Up
════════════════════════════════════════════════════
  Vertex AI  : ✅ Connected
  BigQuery   : ✅ Connected
  MCP SSE    : ✅ Enabled — /sse
════════════════════════════════════════════════════
INFO:     Uvicorn running on http://0.0.0.0:8080
```

> ⚠️ Seeing `⚠️ Demo mode` instead of `✅ Connected`?
> Your GCP credentials are not working. Re-run Step 3.4.

### Step 6.3 — Start Resolution Agent (Terminal 2)

Confirm you are in `services/resolution-agent`, then:

```bash
python main.py
```

Wait for: `INFO: Uvicorn running on http://0.0.0.0:8081`

### Step 6.4 — Start Audit Service (Terminal 3)

Confirm you are in `services/audit-service`, then:

```bash
python main.py
```

Wait for: `INFO: Uvicorn running on http://0.0.0.0:8082`

### Step 6.5 — Verify all 3 services respond

Open a **4th terminal** and run:

**Windows PowerShell:**
```powershell
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

**Mac/Linux:**
```bash
curl -s http://localhost:8080/health | python3 -m json.tool
curl -s http://localhost:8081/health | python3 -m json.tool
curl -s http://localhost:8082/health | python3 -m json.tool
```

# or go the browser and check for these URLs and it should return "OK"

Each must return JSON with `"status": "ok"`. Check specifically:

| Field | Expected | If wrong |
|-------|----------|----------|
| `vertex_ai` | `true` | Re-run Step 3.4 |
| `bigquery` | `true` | Re-run Part 4 |
| `mcp_available` | `true` | Run `pip install mcp` in that service terminal |

### Step 6.6 — Start the React UI (Terminal 4)

In the same 4th terminal:

```bash
cd frontend
npm install --legacy-peer-deps
npm install ajv@^8 --legacy-peer-deps
npm start
```

Your browser opens automatically at **http://localhost:3000** ✅

> ⚠️ **Windows: `Can't resolve './App'` error?**
> Your path contains a `#` character. Move the whole `MCP_IRROPS_Lab` folder to a clean path
> like `C:\Users\YourName\Desktop\MCP_IRROPS_Lab` and restart from Step 6.6.

---

## Part 7 — Verify the Platform is Working

### Check the service status bar

At the top of the UI you will see:
```
MCP SERVICES
🟢 Anomaly Detector :8080    🟢 Resolution Agent :8081    🟢 Audit Service :8082
```

All 3 must be 🟢 green. If any show 🔴 — that service is not running. Go back to Step 6.

### Test Demo 1 — Anomaly Detection

1. Scroll to the **"Real-Time Anomaly Detection Pipeline"** section
2. Click **▶ Start Live Stream**
3. Anomaly cards appear — each one fetched live from BigQuery
4. Each card shows flight number, severity, anomaly type, and Gemini's classification
5. Click **⏹ Stop Stream** when done

### Test Demo 2 — Multi-Agent Resolution

1. Scroll to **"Multi-Agent IRROPS Resolution via MCP"**
2. Click **🚨 Trigger IRROPS → Resolve**
3. Gemini 2.5 Pro creates a resolution plan (takes 5–10 seconds)
4. Each agent step executes: `PENDING → RUNNING → SUCCESS`
5. The result from each tool call appears inline

### Test Demo 3 — Audit Trail

1. Scroll to **"Human-in-the-Loop & Regulatory Audit Trail"**
2. Click **⚡ Simulate Agent Actions**
3. High-confidence actions auto-approve; low-confidence ones escalate to you
4. Click **✓ Approve** or **✗ Reject** for escalated actions
5. Click **📊 Compliance Report** to see the summary

### Confirm BigQuery is receiving audit data

```bash
bq --project_id=your-project-id query --use_legacy_sql=false "SELECT action_id, flight, agent, status, confidence FROM irrops_audit.audit_log ORDER BY assessed_at DESC LIMIT 10"
```

You should see rows for every action taken in the UI.

### Live demo trick — trigger a new anomaly in real time

Open BigQuery Console: https://console.cloud.google.com/bigquery

Run this update query:
```sql
UPDATE irrops_audit.flight_streams
SET delay_min = 210,
    crew_status = 'NO_SHOW',
    updated_at = CURRENT_TIMESTAMP()
WHERE flight = 'AA-301'
```

Then click **⚡ Single Scan** in the UI. A new CRITICAL anomaly for AA-301 appears immediately.

---

## Part 8 — VS Code Debug Launcher

The project already includes `.vscode/launch.json`. You do not need to create it.

**Before using it:** Open `.vscode/launch.json` and replace `YOUR_PROJECT_ID` with your actual project ID in all 3 configurations.

**To use it:**
1. Click the **Run & Debug** icon in the left sidebar (`Ctrl+Shift+D`)
2. Select **🚀 All Services** from the dropdown
3. Click the green ▶ Play button

All 3 services start simultaneously with breakpoint debugging enabled.

---

## Part 9 — Daily Workflow

After first-time setup, your daily routine is:

**Step 1:** Open VS Code in the project folder

**Step 2:** Open 4 terminals (`+` button in terminal panel)

**Step 3:** In each of the 3 service terminals — activate venv and set vars:

```powershell
# Windows (paste into each terminal)
.venv\Scripts\Activate.ps1
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_LOCATION = "us-central1"
$env:GEMINI_MODEL = "gemini-2.5-pro-preview-03-25"
```

```bash
# Mac/Linux (paste into each terminal)
source .venv/bin/activate
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"
export GEMINI_MODEL="gemini-2.5-pro-preview-03-25"
```

**Step 4:** Start each service:

```bash
# Terminal 1
cd services/anomaly-detector && python main.py

# Terminal 2
cd services/resolution-agent && python main.py

# Terminal 3
cd services/audit-service && python main.py

# Terminal 4
cd frontend && npm start
```

**Step 5:** Open http://localhost:3000

---

## 🔧 Troubleshooting Reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| `(.venv)` not showing | venv not activated | `.venv\Scripts\Activate.ps1` (Win) or `source .venv/bin/activate` (Mac) |
| `python: not found` | Python not in PATH | Reinstall Python with "Add to PATH" checked, restart VS Code |
| `gcloud: not found` | gcloud not in PATH | Restart VS Code after gcloud install |
| `npm: not found` | Node.js not installed | Install Node.js 18 LTS, restart VS Code |
| `vertex_ai: false` | ADC not configured | Re-run Step 3.4 |
| `bigquery: false` | BigQuery not set up | Run all of Part 4 |
| Service shows 🔴 in UI | Service not running | Start `python main.py` in the correct terminal |
| `Can't resolve './App'` | `#` in folder path | Move project to a path without special characters |
| `ajv module not found` | Missing npm package | `npm install ajv@^8 --legacy-peer-deps` in frontend folder |
| `signal aborted` | Request timeout | Gemini 2.5 Pro takes 10–15s — already handled, just wait |
| `gemini model not found 404` | API not enabled or wrong name | `gcloud services enable aiplatform.googleapis.com` |
| `BigQuery write failed` | Table doesn't exist | Re-run Part 4 |
| `scripts is disabled` | PowerShell policy | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `pip install` version conflict | Package conflicts | Delete `.venv`, run Step 2.2 again, then reinstall |

---

*AIBEES Labs · MCP_IRROPS_Lab · MCP Enterprise AI Series*
*For issues: open a GitHub issue or contact your instructor*
