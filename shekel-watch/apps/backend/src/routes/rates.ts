import { Router, Request, Response } from 'express';
import { getUsdIlsRate, getAllRates } from '../services/currencyService';
import { logger } from '../utils/logger';

const router = Router();

// GET /api/rates/usd-ils
router.get('/usd-ils', async (_req: Request, res: Response) => {
  try {
    const data = await getUsdIlsRate();
    res.json(data);
  } catch (err) {
    logger.error('Failed to fetch USD/ILS rate', err);
    res.status(500).json({ error: 'Failed to fetch exchange rate' });
  }
});

// GET /api/rates/all
router.get('/all', async (_req: Request, res: Response) => {
  try {
    const data = await getAllRates();
    res.json(data);
  } catch (err) {
    logger.error('Failed to fetch all currency rates', err);
    res.status(500).json({ error: 'Failed to fetch currency rates' });
  }
});

export default router;
