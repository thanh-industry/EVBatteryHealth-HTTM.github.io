# EV Battery State of Health Classification

A full-stack platform for monitoring and classifying the State of Health (SoH) of
electric-vehicle batteries, with three role-based experiences and a real machine
learning pipeline built on scikit-learn.

**State of Health (SoH) is the product metric.** It measures permanent battery
degradation and is not the same as State of Charge (SoC), which is simply how
full the battery is right now. Both exist in the dataset as separate columns and
are never conflated anywhere in this system.

---

## What it does

The platform classifies each battery into one of three health states:

| Class | Label | Rule |
|---|---|---|
| `GOOD` | Good | SoH >= 85% |
| `MONITOR` | Needs Monitoring | 70% <= SoH < 85% |
| `CRITICAL` | Dangerous | SoH < 70% |

Three roles share one integrated backend and data model:

- **Data Scientist** - upload datasets, inspect data quality, train and compare
  SVM / Random Forest / Logistic Regression, deploy the chosen model.
- **EV Technician** - look up a vehicle or battery, run a diagnosis against the
  deployed model, read the recommended action, review diagnostic history.
- **EV User** - a mobile-first view of their own battery: current SoH, trend,
  maintenance advice and alerts.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript 5, Vite 5, Tailwind CSS 3 |
| Charts | Recharts 2 |
| Icons | lucide-react |
| Data fetching | TanStack Query 5 |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Database | SQLite |
| ML | scikit-learn 1.8, pandas, numpy, joblib |
| Tests | pytest (backend), vitest (frontend) |

Vite 5 is used rather than Next.js because the target environment runs Node
18.17, below the Node 18.18+ that current Next.js requires.

---

## Requirements

- Python 3.11 or newer
- Node.js 18.17 or newer
- npm 9 or newer

---

## Quick start (Windows)

```
start-all.cmd
```

This starts the backend, waits until it actually answers, then starts the
frontend. First run takes roughly 60-90 seconds because it installs
dependencies and seeds the database. Then open http://localhost:5173

Use the `.cmd` files rather than the `.ps1` files directly. Many Windows
machines set the PowerShell `LocalMachine` execution policy to `AllSigned` or
`Restricted`, which refuses to run unsigned local scripts and fails with:

```
... is not digitally signed. You cannot run this script on the current system.
```

The `.cmd` wrappers avoid this by passing `-ExecutionPolicy Bypass` for that one
process only. They change nothing on your machine and need no administrator
rights.

If you prefer to run the PowerShell scripts directly, either call them as:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-all.ps1
```

or allow local scripts for your user account once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Available launchers: `start-all.cmd`, `start-backend.cmd`, `start-frontend.cmd`.

## Manual start

Backend (terminal 1):

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.seed
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend (terminal 2):

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` to `http://127.0.0.1:8000`.

---

## Demo accounts

All three use the password `demo1234`.

| Email | Role |
|---|---|
| `scientist@evsoh.io` | Data Scientist |
| `tech@evsoh.io` | EV Technician |
| `owner@evsoh.io` | EV User |

The database is seeded with 60 vehicles and batteries spanning all three health
classes, historical SoH measurements, diagnostics, notifications and maintenance
items, so every screen is populated on first run.

---

## Dataset

The source dataset is `ev battery_failure prediction Dataset.csv`:
20,000 rows and 70 columns of EV telemetry, battery specifications, charging and
driving behaviour, environment and maintenance indicators.

An uploaded CSV must contain a `state_of_health` column. Rows without it cannot
be labelled, so they are dropped for training and the dropped count is reported
in the data quality view rather than discarded silently.

### Excluded columns (label leakage)

Four columns are permanently excluded from every feature matrix because they
restate the label rather than predict it. This was measured, not assumed:

| Column | Reason |
|---|---|
| `state_of_health` | the label source itself |
| `battery_health_percent` | correlates 0.9898 with SoH |
| `capacity_loss_percent` | `battery_health_percent + capacity_loss_percent == 100.0` exactly, standard deviation 0.0 |
| `remaining_capacity` | `remaining_capacity / battery_capacity_kwh * 100` correlates 0.9898 with SoH |

Identifier columns (`vehicle_id`, `battery_serial`) and the secondary
`battery_failure` label are excluded as well.

The rule applied is: **exclude algebraic restatements of the label, but keep
genuine physical sensor readings even when strongly predictive.** For example
`internal_resistance` correlates 0.91 with SoH and is deliberately kept, because
rising internal resistance is how degradation physically manifests and is a value
a technician can actually measure.

The blocklist is enforced in one place (`backend/app/ml/features.py`), asserted
at runtime immediately before every `fit()`, and covered by regression tests.

### Why these thresholds

The 85 / 70 cut points are justified against the independent `battery_failure`
column rather than invented. Observed failure rate per band:

| SoH band | Observed failure rate | Rows |
|---|---|---|
| <= 70 | 27.4% | 2,209 |
| 70 - 85 | 6.7% | 8,982 |
| > 85 | 1.25% | 7,853 |

A roughly 22x failure-rate gradient across the bands confirms the boundaries
carry real meaning. Both thresholds live in `backend/app/core/config.py` and
appear nowhere else in either codebase.

---

## Machine learning

Three algorithms are supported: **Support Vector Machine**, **Random Forest** and
**Logistic Regression**.

The pipeline is built with `sklearn.pipeline.Pipeline` and `ColumnTransformer`:

- Numeric features: median imputation then standard scaling.
- Categorical features: most-frequent imputation then one-hot encoding with
  `handle_unknown="ignore"`.

To prevent data leakage, `train_test_split` runs **before** any fitting, and the
pipeline is fitted on the training partition only. Preprocessing is never fitted
on the full dataset.

Reported metrics are accuracy plus precision, recall and F1 using **macro**
averaging, so the smaller `CRITICAL` class cannot be hidden by the majority
classes. Per-class metrics and a confusion matrix are returned as well. Every
number shown in the interface comes from the API; none are hard-coded.

Measured results on the full dataset (majority-class baseline is 0.471):

| Algorithm | Accuracy | Macro F1 | CRITICAL recall |
|---|---|---|---|
| Random Forest | 0.8711 | 0.8604 | 0.776 |
| Logistic Regression | 0.8698 | 0.8575 | 0.794 |
| SVM | 0.8553 | 0.8406 | 0.746 |

Random Forest has the highest accuracy, but Logistic Regression is better at
catching `CRITICAL` batteries. Since a missed dangerous battery is the costly
error in this domain, the comparison view presents all metrics together rather
than crowning a winner on accuracy alone.

SVM training is capped at 8,000 rows because `SVC` scales superlinearly: the full
15,235-row fit takes 18.2s versus 5.1s at 8,000 rows for a 0.3 percentage point
accuracy difference. The actual row count used is always reported in the
training run so the subsample is never hidden.

---

## Testing

Backend:

```bash
cd backend
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

---

## Project structure

```
backend/
  app/
    api/          one router per endpoint group
    core/         config, security, error handling, recommendations
    db/           session and base
    ml/           features, labeling, pipeline, train, evaluate, registry
    models/       SQLAlchemy entities
    schemas/      Pydantic request and response models
    services/     business logic
    seed.py       seeds the database from the real CSV
  tests/
frontend/
  src/
    components/   reusable UI, charts, tables, layout
    hooks/        data fetching hooks
    lib/          API client, auth, health mapping, query client
    pages/        ds/ technician/ and ev user routes
    types/        TypeScript mirrors of the API contract
```

---

## API overview

Base path `/api`. Interactive documentation is available at
http://127.0.0.1:8000/docs while the backend is running.

| Group | Purpose |
|---|---|
| `/auth` | login, current user |
| `/config` | health thresholds |
| `/datasets` | upload, preview, data quality |
| `/training` | start and poll training runs |
| `/models` | list, active model, deployment |
| `/vehicles`, `/batteries` | lookup and measurements |
| `/diagnostics` | run a diagnosis, history, summary |
| `/me` | EV user battery, history, maintenance |
| `/notifications` | list, mark read |

Errors are returned consistently as `{"detail": "..."}` and stack traces are
never exposed.

---

## Troubleshooting

**"is not digitally signed" / "cannot be loaded".** Your machine's PowerShell
execution policy blocks unsigned local scripts. Run `start-all.cmd` instead of
`start-all.ps1` - see Quick start above. Nothing needs to be changed on your
machine.

**Port already in use.** Stop the process using 8000 or 5173, or change the port
in `frontend/vite.config.ts` and the uvicorn command. If Vite reports "Port 5173
is in use, trying another one" it will serve on 5174 or 5175 instead, but the
`/api` proxy still points at port 8000, so the backend must be on 8000.

**Node version too old.** Vite 5 needs Node 18.17 or newer. Check with
`node --version`.

**Diagnosis returns 409.** No model is deployed yet. Train a model as the Data
Scientist and deploy it first. This is intended behaviour, not a fault.

**Database missing or stale.** Delete `backend/data/app.db` and re-run
`python -m app.seed`.
