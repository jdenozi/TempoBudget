# Tempo Budget

An accessible personal and shared budget management application

## Features

* **Personal budgets**: Expense tracking by category
* **Group budgets**: Sharing with split allocation between members
* **Recurring transactions**: Automatic generation of monthly expenses
* **Projections**: Estimation of upcoming expenses
* **Statistics**: Breakdown by tags (credit, needs, leisure, savings)

## Tech Stack

* **Frontend**: Vue 3 + TypeScript + Naive UI
* **Backend**: FastAPI + SQLite
* **Deployment**: Docker + Nginx

## Local Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
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

## License

MIT
