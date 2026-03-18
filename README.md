# Shekel-Watch

Israeli market dashboard and AI-powered trading assistant. Tracks USD/ILS exchange rates, TASE and dual-listed stocks, paper trading simulation, and arbitrage opportunities between Tel Aviv and New York exchanges.

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit 1.40 (Python) — deployed on **Vercel** |
| **Backend** | Node.js + Express (TypeScript) — deployed on **Railway** |
| **AI Microservice** | FastAPI + CrewAI multi-agent framework |
| **Database / Auth** | Supabase (PostgreSQL + Row-Level Security + Auth) |
| **AI** | OpenAI GPT-4o-mini — bilingual EN/HE summaries & analysis |
| **Messaging** | Green API (WhatsApp) |
| **Charts** | Plotly / Plotly Express |
| **Containerization** | Docker + supervisord (Node + Python in one container) |

---

## Features

### Dashboard
- Real-time USD/ILS exchange rate with source attribution
- AI-generated market summaries in English, Hebrew, and Arabic
- TASE trading phase timer (pre-market / regular / post-market)
- Interactive candlestick charts for historical rate data
- Daily market news feed by region (US / Israel)
- Index tracking: S&P 500, NASDAQ, Dow Jones, TA-35, TA-125

### Paper Trading
- Search and add any TASE / NYSE / NASDAQ instrument to a virtual portfolio
- **Four order types:** Market, Limit, Stop-Loss, Take-Profit
- Visual order-type card selector in the Trade tab
- Pending order monitor (checks every 60 seconds for trigger conditions)
- Full transaction history log
- Portfolio allocation donut chart
- Risk assessment with three experience levels: Beginner / Intermediate / Pro
- Sector diversification breakdown
- AI-powered position suggestions (GPT-4o-mini)
- Virtual cash balance tracked per user

### Arbitrage Scanner
- Dual-listed stock analysis — detects price gaps between TASE and NYSE/NASDAQ
- Gap percentage calculation with direction indicator (BUY TASE / SELL TASE / No Opportunity)
- Auto-refresh every 60 seconds during market hours
- Beginner mode: top-3 opportunities with plain-language explanations
- Pro mode: full filterable table with all metrics

### Watchlist
- Add any ticker to a personal watchlist
- Live price tracking with ILS conversion
- Risk scoring and volatility alerts
- Smart table layout with market indicators

### WhatsApp Bot (Green API)
| Command | Action |
|---|---|
| `Dollar` / `דולר` | Current USD/ILS rate |
| `Status` / `סטטוס` | Full market overview |
| `Summary` | AI summary in English |
| `סיכום` | AI summary in Hebrew |
| `Help` / `עזרה` | Command list |

### Scheduled Background Jobs
| Schedule | Job |
|---|---|
| Daily 05:00–06:00 UTC | Morning WhatsApp alert (bilingual summary + opportunities) |
| Every hour | USD/ILS rate snapshot to database |
| Daily 06:00 UTC (Mon–Fri) | Risk score update for all watchlist items |
| Every 5 min (Mon–Fri 09:00–17:30 IST) | Arbitrage scan for dual-listed gaps |
| Every 10 min | Watchlist volatility monitoring |
| Every 60 sec | Pending order execution check |

---

## Getting Started

### 1. Database Setup

Run each migration in order in your **Supabase SQL Editor** (Project → SQL Editor):

```
supabase/migrations/001_initial_schema.sql
supabase/migrations/002_...sql
...
supabase/migrations/011_pending_order_types.sql
supabase/seed.sql          ← optional sample data
```

### 2. Backend (Node.js)

```bash
cd apps/backend
cp .env.example .env
# Fill in your keys — see Environment Variables below
npm install
npm run dev          # development (ts-node-dev, hot reload)
# OR
npm run build && npm start   # production
```

### 3. Python Microservice (FastAPI + CrewAI)

```bash
cd apps/python
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 4. Streamlit Frontend

```bash
cd apps/streamlit-frontend
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Environment Variables

### Backend (`apps/backend/.env`)

| Variable | Where to get it |
|---|---|
| `PORT` | Port for the Express server (default `3001`) |
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API → `service_role` secret |
| `EXCHANGE_RATE_API_KEY` | https://www.exchangerate-api.com (free tier, used as fallback) |
| `TWELVE_DATA_API_KEY` | https://twelvedata.com (fallback quote source for TASE) |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `GREENAPI_INSTANCE_ID` | https://green-api.com → My Instances |
| `GREENAPI_TOKEN` | https://green-api.com → My Instances → API Token |
| `GREENAPI_WEBHOOK_TOKEN` | Any secret string you choose (validates incoming webhooks) |
| `FRONTEND_URL` | Your streamlit frontend URL, no trailing slash (e.g. `https://shekel-watch.vercel.app`) |

### Streamlit Frontend (`apps/streamlit-frontend/.env`)

| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase → Project Settings → API → `anon` public key |
| `BACKEND_URL` | Your Railway backend URL (e.g. `https://shekel-watch-backend.up.railway.app`). Leave empty for local dev. |

### Python Microservice (`apps/python/.env`)

| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase → Project Settings → API → `anon` public key |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `PYTHON_PORT` | Port for FastAPI service (default `8501`) |

---

## API Endpoints

### Market Data
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/rates/usd-ils` | Live USD/ILS exchange rate with source |
| `GET` | `/api/stocks?tickers=LUMI.TA,TEVA.TA` | Multi-ticker quotes (TASE / NYSE / NASDAQ) |
| `GET` | `/api/arbitrage` | Dual-listed gap analysis with direction |
| `GET` | `/api/summary?lang=en\|he\|ar` | AI-generated market summary |
| `GET` | `/api/market-news?lang=en\|he` | Daily news by region |
| `GET` | `/api/inflation` | Inflation data analysis |

### Paper Trading
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/trade/balance` | Virtual cash balance |
| `GET` | `/api/trade/history?limit=50` | Transaction log |
| `GET` | `/api/trade/pending` | Open conditional orders |
| `POST` | `/api/trade/execute` | Execute a market order |
| `POST` | `/api/trade/order` | Place a limit / stop-loss / take-profit order |
| `DELETE` | `/api/trade/order/:id` | Cancel a pending order |
| `GET` | `/api/portfolio/analysis` | Position analysis |
| `POST` | `/api/portfolio/suggestions` | AI-powered recommendations |

### AI (CrewAI microservice)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/crew/summary` | Multi-agent market analysis |
| `POST` | `/api/crew/compose-alert` | WhatsApp alert generation |
| `POST` | `/api/crew/currency-arbitrage` | Multi-currency opportunity scan |

### Webhooks
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/webhook/whatsapp?token=SECRET` | Green API incoming message handler |

---

## WhatsApp Setup (Green API)

1. Create an account at https://green-api.com and scan the QR code to link your WhatsApp number.
2. In your instance settings, set the webhook URL to:
   ```
   https://<your-railway-url>/api/webhook/whatsapp?token=<GREENAPI_WEBHOOK_TOKEN>
   ```
3. Enable the `incomingMessageReceived` notification type.

---

## Deployment

### Backend → Railway

- Connect your GitHub repo in the Railway dashboard.
- Set root directory to `shekel-watch` and point the build to `apps/backend/Dockerfile`.
- The Dockerfile uses **supervisord** to run both the Node.js backend and the Python FastAPI microservice in one container.
- Add all backend and Python environment variables in Railway → Variables.

### Frontend → Railway

- Add a second Railway service pointing to `shekel-watch/apps/streamlit-frontend`.
- Railway auto-detects `railway.toml` and uses nixpacks to build and run:
  ```
  streamlit run app.py --server.port $PORT --server.headless true
  ```
- Add all Streamlit environment variables including `BACKEND_URL`.

### Database → Supabase

- Run all migrations in order (see Database Setup above).
- Row-Level Security is enabled on all tables — each user only sees their own data.
- An automatic trigger creates a user profile on signup.

---

## Project Structure

```
shekel-watch/
├── apps/
│   ├── backend/                  # Node.js + Express REST API (TypeScript)
│   │   ├── src/
│   │   │   ├── routes/           # API route handlers
│   │   │   ├── services/         # Yahoo Finance, OpenAI, Green API clients
│   │   │   ├── jobs/             # Cron jobs and pending order monitor
│   │   │   └── server.ts         # Entry point
│   │   └── Dockerfile            # Multi-service container (Node + Python)
│   ├── python/                   # FastAPI + CrewAI microservice
│   │   ├── main.py               # Entry point
│   │   └── requirements.txt
│   └── streamlit-frontend/       # Streamlit web UI
│       ├── app.py                # Entry point
│       ├── pages/
│       │   ├── 1_Dashboard.py
│       │   ├── 2_Paper_Trading.py
│       │   ├── 3_Arbitrage_Scanner.py
│       │   ├── 6_Watchlist.py
│       │   └── 7_Profile.py
│       └── requirements.txt
└── supabase/
    ├── migrations/               # SQL schema (001–011)
    └── seed.sql                  # Optional sample data
```
