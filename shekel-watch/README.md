# Shekel-Watch 💰

Israeli market dashboard and AI assistant tracking USD/ILS rates, TASE stocks, and arbitrage gaps for dual-listed companies.

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS (RTL/Hebrew support)
- **Backend**: Node.js + Express on Railway
- **Database/Auth**: Supabase (PostgreSQL)
- **AI**: Google Gemini API
- **Messaging**: Twilio WhatsApp

## Getting Started

### 1. Database Setup
Run the migration in your Supabase SQL editor:
```
supabase/migrations/001_initial_schema.sql
```
Then seed the dual-listed tickers:
```
supabase/seed.sql
```

### 2. Backend
```bash
cd apps/backend
cp .env.example .env
# Fill in your API keys in .env
npm install
npm run dev
```

### 3. Frontend
```bash
cd apps/frontend
cp .env.example .env
# Fill in your Supabase project URL and anon key
npm install
npm run dev
```

## Environment Variables

### Backend (`apps/backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (bypasses RLS) |
| `EXCHANGE_RATE_API_KEY` | exchangerate-api.com key (fallback) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sender (e.g. `whatsapp:+14155238886`) |
| `FRONTEND_URL` | Frontend URL for CORS |

### Frontend (`apps/frontend/.env`)
| Variable | Description |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |

## API Endpoints
- `GET /api/rates/usd-ils` — Live exchange rate
- `GET /api/stocks?tickers=LUMI.TA,TEVA.TA` — TASE/NYSE quotes
- `GET /api/arbitrage` — Dual-listed gap analysis
- `GET /api/summary?lang=en|he` — AI-generated market summary
- `POST /api/webhook/whatsapp` — Twilio WhatsApp webhook

## WhatsApp Commands
- `Dollar` / `דולר` — Current USD/ILS rate
- `Status` / `סטטוס` — Full market overview
- `Summary` — AI summary in English
- `סיכום` — AI summary in Hebrew
- `Help` / `עזרה` — Command list

## Deployment
Backend → Railway (Dockerfile in `apps/backend/Dockerfile`)
Frontend → Vercel (set root to `apps/frontend`, build command `npm run build`)
