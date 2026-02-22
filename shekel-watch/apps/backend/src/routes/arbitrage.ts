import { Router, Request, Response } from 'express';
import { calculateArbitrageGaps } from '../services/arbitrageService';
import { logger } from '../utils/logger';

const router = Router();

// GET /api/arbitrage
router.get('/', async (_req: Request, res: Response) => {
  try {
    const gaps = await calculateArbitrageGaps();
    res.json(gaps);
  } catch (err) {
    logger.error('Failed to calculate arbitrage gaps', err);
    res.status(500).json({ error: 'Failed to calculate arbitrage gaps' });
  }
});

export default router;
