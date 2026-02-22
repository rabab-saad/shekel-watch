import { Router, Request, Response } from 'express';
import { generateMarketSummary } from '../services/geminiService';
import { getUsdIlsRate } from '../services/currencyService';
import { getBatchQuotes } from '../services/yahooFinanceService';
import { calculateArbitrageGaps } from '../services/arbitrageService';
import { logger } from '../utils/logger';

const TASE_TICKERS = ['LUMI.TA', 'HARL.TA', 'TEVA.TA', 'ESLT.TA', 'NICE.TA', 'CHKP.TA'];

const router = Router();

// GET /api/summary?lang=en
router.get('/', async (req: Request, res: Response) => {
  const language = (req.query.lang as 'en' | 'he') === 'he' ? 'he' : 'en';

  try {
    const [rate, stocks, arbitrage] = await Promise.all([
      getUsdIlsRate(),
      getBatchQuotes(TASE_TICKERS),
      calculateArbitrageGaps(),
    ]);

    const summary = await generateMarketSummary({ rate, stocks, arbitrage, language });

    res.json({
      summary,
      language,
      generatedAt: new Date().toISOString(),
    });
  } catch (err) {
    logger.error('Failed to generate market summary', err);
    res.status(500).json({ error: 'Failed to generate market summary' });
  }
});

export default router;
