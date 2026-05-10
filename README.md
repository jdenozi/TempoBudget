<p align="center">
  <img src="docs/logo.png" alt="Tempo Budget Logo" width="150">
</p>

<h1 align="center">Tempo Budget</h1>

<p align="center">
  An accessible personal and shared budget management application
</p>

<p align="center">
  <a href="https://github.com/jdenozi/TempoBudget/actions/workflows/ci.yml">
    <img src="https://github.com/jdenozi/TempoBudget/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <img src="https://img.shields.io/badge/version-2.9.0-blue" alt="Version">
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

### Pro Mode (self-employed / auto-entrepreneur)
* **Multi-regime support**: Pick your legal form — Micro-entrepreneur, Sole proprietorship (real), EURL (with IR/IS option), SASU, SAS — each with its own tax engine
* **Estimated taxes breakdown** on the dashboard: URSSAF contributions, CFP, income tax (withholding or marginal-rate estimate), corporate tax (IS), dividend flat tax, total levies, and net-after-taxes — switchable between monthly, quarterly, and yearly views
* **Adaptive transaction form**: irrelevant fields (products, discounts, gift cards, project link) are hidden for expenses; the client field is relabelled to *supplier* for expenses; required-field validation is enforced
* **Add transaction from anywhere**: the header `+` button now opens a Pro-specific drawer from any Pro view, not just the history
* **Subscriptions / recurring**: dedicated *Subscriptions* view to manage recurring revenue and fixed costs (monthly / weekly / yearly), one-click materialisation of due transactions
* **Customisable revenue limits with chart annotations**: define personal ceilings (e.g. CAF benefits, fiscal thresholds), assigned a name, period and colour, and shown as horizontal lines on the revenue chart with automatic scale conversion between monthly and quarterly views
* **Quarterly chart view**: toggle the revenue evolution chart between monthly (12 months) and quarterly (8 quarters) aggregation
* **"Accounted" toggle on income**: opt a transaction in or out of the URSSAF basis directly when creating it, instead of having to bulk-toggle afterwards
* **Pro / Personal projects separated**: the *Projects* view now filters automatically based on the current Pro/Personal toggle

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

## Recent Changes (v2.9.0)

* Pro mode: multi-regime tax engine (Micro-entrepreneur fully implemented; EI au réel, EURL IR/IS, SASU, SAS supported)
* Pro mode: dashboard "Estimated taxes" card with monthly/quarterly/yearly breakdown of URSSAF, CFP, IR, IS, dividend tax, total levies, and net-after-taxes
* Pro mode: dedicated *Subscriptions* view for recurring revenue and fixed costs, with one-click materialisation of due transactions
* Pro mode: the header `+` button now opens a Pro-specific drawer from any Pro view (dashboard, clients, charts…), not only from the history
* Pro mode: transaction form adapts to expense vs income — products, discounts, gift cards, project link are hidden for expenses; client label becomes *supplier*; required-field validation enforced
* Pro mode: create-time "Accounted" toggle on income transactions (no need to bulk-toggle afterwards)
* Pro mode: customisable revenue limits with horizontal annotations on the revenue chart, with automatic scale conversion between monthly and quarterly views
* Pro mode: monthly / quarterly toggle on the revenue chart and the dashboard tax breakdown
* Pro mode: wording softened — *Declared / Undeclared* renamed to *Accounted / To account*, *URSSAF Declaration* page renamed to *Accounting*
* Pro mode: chart and dashboard cards now consistently say *Turnover* instead of generic *Revenue*
* Projects: the *Projects* view now filters automatically by the current Pro/Personal mode (the manual filter buttons were removed)

## License

MIT
