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
  <img src="https://img.shields.io/badge/version-2.10.0-blue" alt="Version">
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
* **Estimated taxes breakdown** on the dashboard: URSSAF contributions, CFP, income tax (withholding or marginal-rate estimate), corporate tax (IS), dividend flat tax, total levies, *Net to you* and net-after-taxes — switchable between monthly, quarterly, and yearly views, with a year picker for historical reviews
* **Compare regimes side-by-side**: a one-click modal that runs every regime (Micro / EI réel / EURL IR-IS / SASU / SAS) on your current activity and ranks them by personal take-home. An inline hint on the dashboard surfaces the optimal regime when it differs from your current one
* **Tracked limits dashboard**: one progress bar per user-defined revenue threshold (Prime d'activité, micro-ceilings, custom goals…), period-aware (monthly / quarterly / yearly) with green / orange / red colour coding
* **Tax-deductible flag on expenses**: mark which charges enter the bénéfice computation for EI / EURL / SASU / SAS regimes (defaults to deductible; non-deductible entries get a warning chip in the history)
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

## Recent Changes (v2.10.0)

* Pro mode: *Compare regimes* modal — runs every regime (Micro / EI réel / EURL IR-IS / SASU / SAS) on your current activity, ranks by personal take-home, highlights the optimal regime
* Pro mode: inline "switch regime" hint on the dashboard tax breakdown — clickable when a different regime would let you net more for the period
* Pro mode: dashboard *Tracked limits* card with a progress bar per user-defined threshold (period-aware, colour-coded by proximity)
* Pro mode: tax breakdown now exposes *Net to you* (= net salary − personal IR + dividends after flat tax for incorporated regimes; equals net-after-taxes for non-incorporated)
* Pro mode: tax-deductible flag on expense transactions, surfaced as a switch in the form and a warning chip in history; only deductible charges enter the bénéfice computation for EI / EURL / SASU / SAS
* Pro mode: dashboard "Estimated contributions" card now uses the active regime's engine instead of the micro formula (correct figures for SASU / SAS / EURL)
* Pro mode: year selector on the dashboard tax breakdown and the regime comparison modal — review past-year totals when filing taxes

## License

MIT
