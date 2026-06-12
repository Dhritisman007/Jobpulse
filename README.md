# Remote Job Search Automation Tool — JobPulse ⚡

A full-stack job aggregation, matching, and application-assist platform for freshers seeking remote internships and entry-level tech roles.

## Features

- **Job Aggregation** — Fetches from 5 public APIs: RemoteOK, Remotive, WeWorkRemotely (RSS), Arbeitnow, Jobicy
- **Smart Matching** — Scores jobs 0–100 against your resume (skills, frameworks, category, experience level, recency)
- **Premium Dashboard** — Dark glassmorphism React UI with filtering, sorting, and pagination
- **Application Tracking** — Mark jobs as Applied/Interested/Skip, add notes, track history
- **Cover Letter Generator** — Claude AI-powered tailored cover letters per job
- **Manual Import** — Add LinkedIn/Wellfound/Internshala jobs manually
- **Daily Digest** — Telegram + Email notifications for new matching jobs

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Edit with your API keys

# Edit resume.json with your details

uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open Dashboard
Navigate to **http://localhost:5173**

Click **"Refresh Jobs"** to trigger the first scrape.

## Configuration

Edit `backend/.env`:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | For cover letters | Claude API key |
| `TELEGRAM_BOT_TOKEN` | For notifications | Telegram bot token |
| `TELEGRAM_CHAT_ID` | For notifications | Your Telegram chat ID |
| `SMTP_USER` / `SMTP_PASSWORD` | For email digest | Gmail app password |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/jobs` | List jobs with filters |
| POST | `/api/jobs/refresh` | Trigger full scrape |
| POST | `/api/jobs/import` | Manual job import |
| GET | `/api/jobs/stats` | Dashboard statistics |
| PUT | `/api/applications/{id}` | Update application status |
| POST | `/api/cover-letters/generate` | Generate cover letter |
| POST | `/api/rescore` | Re-score all jobs |
| POST | `/api/notify` | Send digest manually |

## Data Sources

| Source | Method | ToS-Compliant |
|---|---|---|
| RemoteOK | Public JSON API | ✅ |
| Remotive | Public REST API | ✅ |
| WeWorkRemotely | Public RSS Feed | ✅ |
| Arbeitnow | Public JSON API | ✅ |
| Jobicy | Public JSON API | ✅ |
| LinkedIn | Manual import only | ✅ |
| Wellfound | Manual import only | ✅ |
| Internshala | Manual import only | ✅ |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, SQLite, httpx
- **Frontend**: React 18, Vite, Vanilla CSS
- **AI**: Claude API (Anthropic)
- **Notifications**: Telegram Bot API, SMTP

## License

MIT — Personal use project
