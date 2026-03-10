# Shekel-Watch

Israeli market dashboard and AI assistant tracking USD/ILS rates, TASE stocks, and arbitrage gaps for dual-listed companies.

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS (RTL/Hebrew support) → deployed on **Vercel**
- **Backend**: Node.js + Express → deployed on **Railway**
- **Database/Auth**: Supabase (PostgreSQL + Auth)
- **AI**: OpenAI API (GPT-4o-mini) — bilingual EN/HE market summaries
- **Messaging**: Green API (WhatsApp)

## Getting Started

### 1. Database Setup
Run in your Supabase SQL editor (Project → SQL Editor):
```
supabase/migrations/001_initial_schema.sql
supabase/seed.sql
```

### 2. Backend
```bash
cd apps/backend
cp .env.example .env
# Fill in your keys — see Environment Variables below
npm install
npm run dev
```

### 3. Frontend
```bash
cd apps/frontend
cp .env.example .env
# Fill in VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
npm install
npm run dev
```

## Environment Variables

### Backend (`apps/backend/.env`)
| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API → `service_role` secret (JWT, starts with `eyJ`) |
| `EXCHANGE_RATE_API_KEY` | https://www.exchangerate-api.com (free tier) |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `GREENAPI_INSTANCE_ID` | https://green-api.com → My Instances |
| `GREENAPI_TOKEN` | https://green-api.com → My Instances → API Token |
| `GREENAPI_WEBHOOK_TOKEN` | Any secret string you choose (used to validate incoming webhooks) |
| `FRONTEND_URL` | Your Vercel frontend URL, no trailing slash (e.g. `https://shekel-watch.vercel.app`) |

### Frontend (`apps/frontend/.env`)
| Variable | Where to get it |
|---|---|
| `VITE_SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase → Project Settings → API → `anon` public key |
| `VITE_BACKEND_URL` | Your Railway backend URL (e.g. `https://shekel-watch-backend.up.railway.app`). Leave empty for local dev. |

## API Endpoints
- `GET /api/rates/usd-ils` — Live USD/ILS exchange rate
- `GET /api/stocks?tickers=LUMI.TA,TEVA.TA` — TASE/NYSE quotes
- `GET /api/arbitrage` — Dual-listed gap analysis
- `GET /api/summary?lang=en|he` — AI-generated market summary
- `POST /api/webhook/whatsapp?token=SECRET` — Green API WhatsApp webhook

## WhatsApp Commands
- `Dollar` / `דולר` — Current USD/ILS rate
- `Status` / `סטטוס` — Full market overview
- `Summary` — AI summary in English
- `סיכום` — AI summary in Hebrew
- `Help` / `עזרה` — Command list

## WhatsApp Setup (Green API)
1. Create an account at https://green-api.com and scan the QR code to link your WhatsApp
2. In your instance settings, set the webhook URL to:
   `https://<your-railway-url>/api/webhook/whatsapp?token=<GREENAPI_WEBHOOK_TOKEN>`
3. Enable the `incomingMessageReceived` notification type

## Deployment

### Backend → Railway
- Connect your GitHub repo in Railway dashboard
- Set root directory to `shekel-watch`, build with the `apps/backend/Dockerfile`
- Add all backend environment variables in Railway → Variables

### Frontend → Vercel
- Connect your GitHub repo in Vercel dashboard
- Set **Root Directory** to `shekel-watch/apps/frontend`
- Build command: `npm run build` | Output directory: `dist`
- Add all frontend environment variables including `VITE_BACKEND_URL`
