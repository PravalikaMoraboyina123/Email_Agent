# InboxPilot AI 🤖📧
> **Production-Grade, 100% Free Autonomous Personal AI Email Agent**

InboxPilot AI is an autonomous, 24/7 background AI assistant built with **Python**, **FastAPI**, **SQLite**, **Gmail API (Google OAuth 2.0)**, **Ollama (Local LLM)**, **APScheduler**, and **gTTS (Text-to-Speech)**.

It continuously monitors your Gmail inbox, analyzes email urgency & Data Science/Career opportunities using local AI, speaks urgent notifications aloud, executes automated **6:00 AM Morning Briefings** and **9:00 PM Evening Reviews**, and self-learns from your open/ignore interaction history without any paid API keys or cloud subscriptions.

---

## ✨ Features

- 🆓 **100% FREE & Private**: Powered by local Ollama LLMs (`llama3.2` / `mistral`). Zero paid API tokens or subscription costs.
- 🔑 **Hands-Free Gmail OAuth 2.0**: Authorize once; auto-refreshes tokens silently in the background 24/7.
- ⏰ **Automated Daily Routines**:
  - **6:00 AM Morning Briefing**: Summarizes unread high-priority emails, deadlines, and recommended actions aloud.
  - **9:00 PM Evening Briefing**: Reviews today's email volume and highlights uncompleted urgent opportunities before sleeping.
  - **Continuous Live Scanner**: Checks inbox every 5 minutes for urgent placement, assessment, or interview invites.
- 🎯 **Intelligent Categorization & Opportunity Scoring**:
  - Scores urgency (0–100) and Career Opportunity Score (0–100) based on Data Science career fit, deadline, and role prestige.
  - Automatically filters out advertisements, spam, and promotional marketing.
- 🧠 **Adaptive Learning Memory**: Dynamically boosts priority for senders/categories you open frequently and penalizes ignored email sources.
- 🗣️ **Natural Voice Synthesis**: Natural text-to-speech rendering via `gTTS` with async non-blocking audio playback.
- ⚡ **Production Architecture**: Built using Clean Architecture (Domain Models, Pydantic Schemas, Services, Memory, Cron Scheduler, REST API).

---

## 🏗️ Project Architecture

```
inboxpilot/
├── config/             # Environment settings & Pydantic validation
├── database/           # SQLite engine & SQLAlchemy 2.0 session factory
├── models/             # SQLAlchemy ORM tables & Pydantic JSON schemas
├── prompts/            # Ollama prompt engineering templates
├── services/           # Gmail OAuth, Ollama LLM, gTTS Voice, Learning Engine
├── memory/             # Deduplication state & audit log memory
├── agents/             # Autonomous InboxPilot Agent orchestrator
├── scheduler/          # APScheduler 24/7 background daemon
├── routers/            # FastAPI REST endpoints & control dashboard
├── utils/              # Centralized logging & helper utilities
├── tests/              # Pytest test suite
├── main.py             # FastAPI Application lifespan entrypoint
├── Dockerfile          # Production Docker container image
├── docker-compose.yml  # Docker Compose service definition
└── README.md           # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.11+**
- **Ollama**: Download & install from [ollama.com](https://ollama.com). Pull your model:
  ```bash
  ollama pull llama3.2
  ```
- **Google Cloud OAuth Credentials**:
  1. Go to [Google Cloud Console](https://console.cloud.google.com/).
  2. Create a project, enable the **Gmail API**.
  3. Create an **OAuth 2.0 Client ID** (Application type: *Desktop App*).
  4. Download JSON credentials and save as `credentials.json` in project root directory.

### 2. Installation & Setup
```bash
# Clone repository
git clone https://github.com/your-username/inboxpilot-ai.git
cd inboxpilot-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
```

### 3. Run FastAPI Application & Agent
```bash
python main.py
```
Or with Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```
Interactive API documentation will be available at: `http://localhost:8000/docs`

---

## 🔌 First-Time Google OAuth Authorization
On your first startup, visit:
`http://localhost:8000/auth/authorize`

A browser tab will open asking you to sign into your Google Account and grant read/modify permissions to InboxPilot AI. Once authorized, `token.json` will be saved locally. InboxPilot AI will run automatically without requiring manual authorization logins again.

---

## 🤖 Continuous 24/7 Background Daemon Setup (Linux Systemd)

To make InboxPilot AI start automatically whenever your laptop boots up and run continuously in the background:

### 1. User Systemd Service Installation
InboxPilot AI runs as a Linux user service so it has access to your desktop audio drivers for voice briefings.

Create or update `~/.config/systemd/user/inboxpilot.service`:
```ini
[Unit]
Description=InboxPilot AI Autonomous Agent Service
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/anusha/email agent
ExecStart="/home/anusha/email agent/venv/bin/python" main.py
Restart=always
RestartSec=10
Environment="PATH=/home/anusha/email agent/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
```

### 2. Enable & Start Service
```bash
# Reload systemd user configuration
systemctl --user daemon-reload

# Enable service to start on boot
systemctl --user enable inboxpilot.service

# Start the service immediately
systemctl --user start inboxpilot.service

# Verify service is running
systemctl --user status inboxpilot.service
```

### 3. Service Commands
- **View Live Logs**:
  ```bash
  journalctl --user -u inboxpilot.service -f
  ```
- **Restart Service**:
  ```bash
  systemctl --user restart inboxpilot.service
  ```
- **Stop Service**:
  ```bash
  systemctl --user stop inboxpilot.service
  ```
- **Check Diagnostics & System Health**:
  ```bash
  curl http://127.0.0.1:8000/health
  ```

---

## 🏥 Health Endpoint Diagnostics (`/health`)
Query the system health endpoint anytime to inspect component status:
```json
{
  "status": "healthy",
  "gmail_connected": true,
  "user_email": "pravalikamoraboyina21@gmail.com",
  "ollama_available": true,
  "scheduler_running": true,
  "email_check_interval_seconds": 60,
  "last_scan_time": "2026-08-08T14:20:00+00:00",
  "total_processed_emails": 45,
  "total_important_emails": 12
}
```

---

## 🧪 Running Tests
Execute unit tests using pytest:
```bash
"/home/anusha/email agent/venv/bin/pytest" -v
```

---

## 📜 License
MIT License. Free for open source, personal, and educational use.
