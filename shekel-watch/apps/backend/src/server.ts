import express from 'express';
import helmet from 'helmet';
import cors from 'cors';

const app = express();

// ─── Health — always first, no config dependency ──────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ─── Start listening immediately so Railway healthcheck always passes ─────────
const port = parseInt(process.env.PORT || '3001', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`Server listening on port ${port} — env: ${process.env.NODE_ENV || 'development'}`);
  // Initialize the rest of the app after server is already up
  bootstrap().catch(err => {
    console.error('Bootstrap failed — API routes unavailable:', err.message);
  });
});

async function bootstrap() {
  // Dynamic imports so config errors don't prevent server from starting
  const { config }       = await import('./config');
  const { rateLimiter }  = await import('./middleware/rateLimiter');
  const { router }       = await import('./routes');
  const { startScheduler } = await import('./jobs/scheduler');
  const { logger }       = await import('./utils/logger');

  app.use(helmet());
  app.use(cors({ origin: config.FRONTEND_URL }));
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  app.use(rateLimiter);
  app.use('/api', router);

  startScheduler();
  logger.info(`Shekel-Watch fully initialized on port ${port}`);
}

export default app;
