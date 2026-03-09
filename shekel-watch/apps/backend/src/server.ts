import './config';  // Validates env vars first — crashes fast if invalid
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { config } from './config';
import { rateLimiter } from './middleware/rateLimiter';
import { router } from './routes';
import { startScheduler } from './jobs/scheduler';
import { logger } from './utils/logger';

const app = express();

// ─── Security & Parsing ──────────────────────────────────────────────────────
app.use(helmet());
app.use(cors({ origin: config.FRONTEND_URL }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(rateLimiter);

// ─── Routes ──────────────────────────────────────────────────────────────────
app.use('/api', router);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ─── Cron Jobs ───────────────────────────────────────────────────────────────
startScheduler();

// ─── Start Server ────────────────────────────────────────────────────────────
app.listen(Number(config.PORT), () => {
  logger.info(`Shekel-Watch backend running on port ${config.PORT}`);
});

export default app;
