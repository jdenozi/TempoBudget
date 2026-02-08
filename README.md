<p align="center">
  <img src="docs/logo.png" alt="Tempo Finance Logo" width="150">
</p>

<h1 align="center">Tempo Finance</h1>

<p align="center">
  An accessible personal and shared budget management application
</p>

<p align="center">
  <a href="https://github.com/jdenozi/TempoBudget/actions/workflows/ci.yml">
    <img src="https://github.com/jdenozi/TempoBudget/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <img src="https://img.shields.io/badge/version-0.14.1-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

## Features

### Budget Management
* **Personal budgets**: Expense tracking by category with subcategories
* **Group budgets**: Sharing with split allocation between members
* **Balance tracking**: See who owes what in shared budgets

### Transactions
* **Recurring transactions**: Automatic generation of monthly/weekly/yearly expenses
* **Version history**: Track changes to recurring transactions with effective dates
* **Date filtering**: Filter transactions and recurring by date range

### Analytics
* **Projections**: Estimation of upcoming expenses based on recurring transactions
* **Projected remaining**: See remaining budget after projected expenses
* **Statistics**: Breakdown by tags (credit, needs, leisure, savings)
* **Charts**: Visual representation of spending patterns

## Tech Stack

* **Frontend**: Vue 3 + TypeScript + Naive UI
* **Backend**: FastAPI + SQLite
* **Deployment**: Docker + Nginx

## Local Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure your JWT_SECRET
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Docker Deployment

```bash
cp .env.example .env
# Edit .env with a JWT_SECRET generated via: openssl rand -hex 32

docker-compose -f docker-compose.prod.yml up -d
```

The application is accessible on port 80.

## Recent Changes (v0.14.0)

* Date range filter in Recurring and History views
* Projected totals calculation for selected periods
* Fixed remaining/projected remaining display for subcategories

## License

MIT
