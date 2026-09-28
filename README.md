# Budget Buddy 💰

**Smart Finance for College Students** — College Academic Project

A web application that helps college students track income/expenses, analyze spending, create adaptive budgets, predict future spending, and get personalized AI financial guidance.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🧾 Receipt Scanner | Upload receipt → OCR → AI parses data → Save expense |
| 🧠 AI Categorization | Auto-categorizes expenses using GroqAI |
| 📊 Adaptive Budget Engine | Recommends budgets based on income & spending |
| 🔮 Spending Prediction | Estimates monthly spending with optional ML |
| ⚡ Budget Risk Detection | Alerts for rapid spending, overbudget, savings risk |
| 💬 AI Financial Coach | Natural-language financial Q&A with full context |
| 🎯 What-If Simulator | Test hypothetical decisions without real data changes |
| 🎯 Savings Goals | Create and track savings targets |

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Backend**: Python 3.10+, Flask
- **Auth & Database**: Supabase (Auth + PostgreSQL)
- **AI**: OpenAI API (GPT-4o-mini)
- **OCR**: Tesseract OCR + Pillow
- **Analysis**: Pandas
- **Prediction**: Scikit-learn (optional, ML fallback)

---

## 📋 Setup Instructions

### 1. Clone & Create Virtual Environment

```bash
cd budget-buddy
python -m venv venv
venv\Scripts\activate      # Windows
# OR
source venv/bin/activate   # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual keys
```

Fill in `.env`:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-...
FLASK_SECRET_KEY=generate-a-random-secret-key
```

### 4. Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a project
2. Open **SQL Editor** and run the contents of `supabase_schema.sql`
3. Get your **Project URL** and **Anon Key** from Settings → API

### 5. Install Tesseract OCR (for Receipt Scanner)

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH, OR set `TESSERACT_CMD` in `.env`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### 6. Run the Application

```bash
python run.py
```

Open: http://localhost:5000

---

## 📁 Project Structure

> 💡 **Detailed Architecture Guide**: See [PROJECT_STRUCTURE.md](file:///e:/projects/Budget_buddy/PROJECT_STRUCTURE.md) for a full layer-by-layer breakdown of every route, service, and component.

```
budget-buddy/
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── routes/             # Flask blueprints (auth, dashboard, transactions, etc.)
│   ├── services/           # Business logic & AI (supabase, openai, ocr, analytics)
│   ├── utils/              # Helpers & decorators
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS, images, uploads
├── components/             # React / shadcn UI components
├── lib/                    # Frontend utility functions
├── styles/                 # Tailwind CSS & design tokens
├── tests/                  # Pytest test suite
├── supabase_schema.sql     # Database schema
├── requirements.txt
├── package.json
├── tsconfig.json
├── run.py                  # Server entry point
└── README.md
```

---

## 🏗️ Application Flow

```
Landing Page → Login/Register → Dashboard
→ Add Income/Expense (Manual OR Receipt Scanner)
→ AI Auto-Categorization
→ Spending Analysis (Pandas)
→ Adaptive Budget + Prediction (Python/ML)
→ Budget Risk Detection
→ AI Financial Coach (OpenAI)
→ What-If Simulator
```

---

## ⚠️ Disclaimer

Budget Buddy is a **college academic project**. AI recommendations are for **educational budgeting assistance only** and do not constitute professional financial advice.

---

## 📊 Database Tables

- `profiles` — User profile with monthly income
- `transactions` — Income and expense records
- `budgets` — Monthly budget limits and savings targets
- `budget_categories` — Per-category spending limits
- `savings_goals` — User savings targets with progress

All tables use **Supabase Row Level Security (RLS)** — users can only access their own data.
