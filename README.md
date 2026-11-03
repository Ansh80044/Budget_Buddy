# Budget Buddy

### AI-Powered Smart Finance Manager for College Students

Budget Buddy helps college students take control of their finances — track every rupee, scan receipts with AI, get personalized budget recommendations, predict future spending, and chat with an AI financial coach. Built as a college academic project, it's a full-featured MVP that turns chaotic student spending into actionable insights.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Application Flow](#application-flow)
- [Routes & Endpoints](#routes--endpoints)
- [Database Schema](#database-schema)

---

## Features

### Core
- Secure authentication (email/password + Google OAuth via Supabase)
- Dashboard with spending charts, budget status, risk alerts, and recent transactions
- Add, edit, and delete income/expense transactions with search and filters
- Receipt scanner — upload a photo, OCR extracts text, AI parses merchant, amount, date, and items
- AI-powered auto-categorization across 15 student-friendly categories using Groq AI
- Local-first architecture — works fully offline with SQLite, zero external API keys required

### Intelligence
- Adaptive budget engine — AI-generated budget recommendations based on income and spending history
- Spending prediction — forecasts monthly spending using scikit-learn ML (with daily-average fallback)
- Budget risk detection — alerts for rapid spending, predicted overflow, category limit violations, and savings risk
- AI financial coach — ask natural-language questions about your finances with full context
- What-if simulator — test hypothetical scenarios (purchases, spending cuts, income changes) without affecting real data

### Goals
- Create and track savings goals with target amounts and deadlines
- Make contributions and see visual progress toward each goal

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask |
| Frontend | Jinja2 Templates, Custom CSS Design System |
| Landing Page | React, TypeScript, Tailwind CSS, Framer Motion, shadcn/ui |
| Database | Supabase (PostgreSQL + RLS) with SQLite fallback |
| AI / LLM | Groq AI (preferred, free) or OpenAI (gpt-4o-mini) |
| OCR | Tesseract OCR + Pillow |
| Data Analysis | Pandas, NumPy |
| ML | Scikit-learn (LinearRegression) |
| Charts | Chart.js |
| Production Server | Gunicorn |

---

## Project Structure

```text
Budget_buddy/
├── app/
│   ├── __init__.py                # Flask app factory, registers 9 Blueprints
│   ├── routes/
│   │   ├── auth.py                # Login, register, logout, OAuth callback
│   │   ├── dashboard.py           # Dashboard overview
│   │   ├── transactions.py        # Transaction CRUD + AI categorize API
│   │   ├── budget.py              # Budget planner + AI recommendations
│   │   ├── reports.py             # Reports, analytics, and trend charts
│   │   ├── goals.py               # Savings goals CRUD + contributions
│   │   ├── receipt.py             # Receipt upload, OCR scan, and save
│   │   ├── ai.py                  # AI Financial Coach chat
│   │   └── simulator.py           # What-If scenario runner
│   ├── services/
│   │   ├── supabase_service.py    # DB abstraction (Supabase + SQLite fallback)
│   │   ├── local_db.py            # SQLite implementation for offline mode
│   │   ├── ai_service.py          # Groq/OpenAI: categorization, parsing, coaching
│   │   ├── analysis_service.py    # Pandas-based spending analytics
│   │   ├── budget_service.py      # Budget recommendations and risk detection
│   │   ├── prediction_service.py  # ML spending predictions
│   │   └── ocr_service.py         # Tesseract OCR multi-pass extraction
│   ├── utils/
│   │   └── helpers.py             # login_required decorator, date/number helpers
│   ├── templates/                 # Jinja2 HTML templates
│   │   ├── base.html              # Layout shell with sidebar navigation
│   │   ├── index.html             # Animated landing page
│   │   ├── login.html             # Login form
│   │   ├── register.html          # Registration with monthly income field
│   │   ├── dashboard.html         # Dashboard with charts and risk alerts
│   │   ├── transactions.html      # Transaction ledger with add/edit modals
│   │   ├── budget.html            # Budget planner with category limits
│   │   ├── reports.html           # Analytics and trend charts
│   │   ├── goals.html             # Savings goals with progress bars
│   │   ├── receipt.html           # Receipt upload and OCR scanner
│   │   ├── coach.html             # AI Financial Coach chat UI
│   │   └── simulator.html         # What-If scenario sandbox
│   └── static/
│       ├── css/style.css          # Fintech design system (Plus Jakarta Sans, Inter)
│       ├── images/                # Hero images, screenshots
│       └── uploads/               # Temporary receipt uploads
├── components/ui/                 # React + shadcn landing page components
├── lib/                           # Frontend utility functions
├── styles/                        # Tailwind CSS globals and design tokens
├── tests/                         # Pytest test suite
├── supabase_schema.sql            # Database schema (run in Supabase SQL Editor)
├── requirements.txt               # Python dependencies
├── package.json                   # NPM deps + dev/test scripts
└── run.py                         # Server entry point
```

---

## Getting Started

### 1. Clone and create a virtual environment

```bash
cd Budget_buddy
python -m venv venv
venv\Scripts\activate          # Windows
# OR
source venv/bin/activate       # Linux / macOS
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node dependencies (optional, for landing page components)

```bash
npm install
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```env
SUPABASE_URL=https://your-project-id.supabase.co    # optional — SQLite fallback if omitted
SUPABASE_KEY=your-anon-key                           # optional
GROQ_API_KEY=your-groq-api-key                       # optional — rule-based fallback if omitted
OPENAI_API_KEY=sk-...                                # optional — alternative to Groq
FLASK_SECRET_KEY=generate-a-random-secret-key
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe   # Windows only, optional
```

> **Zero-config mode:** The app runs with no `.env` at all — SQLite auto-creates for storage and rule-based logic handles categorization. Add API keys only when you want cloud DB or AI features.

### 5. Set up the database (choose one)

**Option A — Local SQLite (zero config):**
Just run the app. The database auto-creates at `app/budget_buddy_local.db`.

**Option B — Supabase (cloud):**
1. Create a project at [supabase.com](https://supabase.com)
2. Open **SQL Editor** and run the contents of `supabase_schema.sql`
3. Copy your **Project URL** and **Anon Key** from Settings → API into `.env`

### 6. Install Tesseract OCR (optional, for receipt scanning)

**Windows:**
- Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- Install and add to PATH, or set `TESSERACT_CMD` in `.env`

**Linux / macOS:**
```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### 7. Run

```bash
python run.py
```

Open: [http://localhost:5000](http://localhost:5000)

**Alternative npm scripts:**
```bash
npm run dev     # runs python run.py
npm run test    # runs pytest
```

---

## Application Flow

1. Land on the **home page** (`/`) — animated hero section with feature showcase
2. **Register** with name, email, password, and monthly income/stipend
3. **Log in** and land on the **Dashboard** — spending summary, charts, risk alerts, predictions
4. **Add transactions** manually or use the **Receipt Scanner** to upload a photo
   - OCR extracts text → AI parses merchant, amount, date → auto-categorizes and saves
5. **Plan your budget** — set monthly limits, per-category caps, get AI recommendations
6. **Track savings goals** — create targets, make contributions, see progress
7. **View reports** — category breakdowns, monthly trends, largest expenses, ML predictions
8. **Ask the AI Coach** anything about your finances in plain English
9. **Run what-if simulations** — "What if I buy a ₹3,000 laptop bag?" without affecting real data
10. Get **risk alerts** automatically when spending is too rapid or budget is at risk

---

## Routes & Endpoints

### Public Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Landing page (redirects to dashboard if logged in) |
| `GET` | `/login` | Login page |
| `POST` | `/login` | Process login |
| `GET` | `/register` | Registration page |
| `POST` | `/register` | Process registration |
| `GET` | `/logout` | Sign out and clear session |

### Protected Page Routes (redirects to login if not authenticated)

| Method | Path | Description |
|---|---|---|
| `GET` | `/dashboard` | Main dashboard overview |
| `GET` | `/transactions` | Transaction ledger |
| `POST` | `/transactions/add` | Add new transaction |
| `GET/POST` | `/transactions/<id>/edit` | Edit transaction |
| `POST` | `/transactions/<id>/delete` | Delete transaction |
| `GET` | `/budget` | Budget planner page |
| `POST` | `/budget/save` | Save monthly budget and category limits |
| `GET` | `/reports` | Reports and analytics |
| `GET` | `/goals` | Savings goals page |
| `POST` | `/goals/add` | Create savings goal |
| `POST` | `/goals/<id>/update` | Update goal details |
| `POST` | `/goals/<id>/delete` | Delete goal |
| `POST` | `/goals/<id>/contribute` | Add contribution to goal |
| `GET` | `/receipt` | Receipt scanner page |
| `POST` | `/receipt/scan` | Upload and OCR process receipt |
| `POST` | `/receipt/save` | Save scanned receipt as transaction |
| `GET` | `/coach` | AI Financial Coach chat page |
| `GET` | `/simulator` | What-If Simulator page |

### API Routes (returns JSON)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/categorize` | AI auto-categorize an expense description |
| `GET` | `/api/transactions` | Get all transactions as JSON |
| `POST` | `/api/budget/recommend` | Get AI budget recommendation |
| `GET` | `/api/reports/data` | Get full reports data as JSON |
| `POST` | `/api/coach/ask` | Ask the AI financial coach a question |
| `POST` | `/api/simulator/run` | Run a what-if simulation scenario |

---

## Database Schema

All tables use **Supabase Row Level Security (RLS)** — users can only access their own data. Tables are mirrored in SQLite for offline mode.

| Table | Description |
|---|---|
| `profiles` | User profile with name, email, and monthly income |
| `transactions` | Income/expense records with amount, category, date, source (manual or receipt) |
| `budgets` | Monthly budget limits and savings targets (unique per user per month) |
| `budget_categories` | Per-category spending limits linked to a budget |
| `savings_goals` | Savings targets with name, target amount, saved amount, and deadline |

### Expense Categories (15)

Food & Dining · Transportation · Shopping · Entertainment · Education · Health & Medical · Utilities · Rent & Housing · Personal Care · Travel · Subscriptions · Groceries · Sports & Fitness · Gifts & Donations · Other

---

## Testing

```bash
python -m pytest tests/
```

| Test File | Coverage |
|---|---|
| `test_routes.py` | Route status codes and auth redirect checks |
| `test_services.py` | Analysis, prediction, budget, and categorization unit tests |
| `test_decision_support.py` | AI Coach and Simulator integration tests |

---

