import { Router, Request, Response } from 'express';
import { getBatchQuotes, getQuote, getHistory } from '../services/yahooFinanceService';
import { logger } from '../utils/logger';

const router = Router();

// GET /api/stocks?tickers=LUMI.TA,TEVA.TA
router.get('/', async (req: Request, res: Response) => {
  const raw = (req.query.tickers as string) ?? '';
  const tickers = raw.split(',').map(t => t.trim()).filter(Boolean);

  if (!tickers.length) {
    res.status(400).json({ error: 'Provide at least one ticker via ?tickers=X,Y' });
    return;
  }

  try {
    const quotes = await getBatchQuotes(tickers);
    res.json(quotes);
  } catch (err) {
    logger.error('Failed to fetch batch quotes', err);
    res.status(500).json({ error: 'Failed to fetch stock data' });
  }
});

// GET /api/stocks/:ticker/history?period=3mo
router.get('/:ticker/history', async (req: Request, res: Response) => {
  const period = (req.query.period as string) || '3mo';
  try {
    const bars = await getHistory(req.params.ticker, period as any);
    res.json(bars);
  } catch (err) {
    logger.error(`Failed to fetch history for ${req.params.ticker}`, err);
    res.status(500).json({ error: `Failed to fetch history for ${req.params.ticker}` });
  }
});

// GET /api/stocks/:ticker
router.get('/:ticker', async (req: Request, res: Response) => {
  try {
    const quote = await getQuote(req.params.ticker);
    res.json(quote);
  } catch (err) {
    logger.error(`Failed to fetch quote for ${req.params.ticker}`, err);
    res.status(404).json({ error: `No data found for ticker: ${req.params.ticker}` });
  }
});

export default router;
