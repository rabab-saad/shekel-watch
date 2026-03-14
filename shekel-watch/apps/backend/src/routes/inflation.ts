import { Router, Request, Response } from 'express';
import axios from 'axios';
import { getUsdIlsRate } from '../services/currencyService';
import { logger } from '../utils/logger';

const router = Router();

// USD/ILS rate in January 2020 (historical anchor)
const USD_ILS_BASELINE_2020 = 3.456;

interface InflationCache {
  data:      InflationPayload;
  expiresAt: number;
}

interface InflationPayload {
  cpiCurrent:          number;
  cpiBaseline2020:     number;
  usdIls:              number;
  usdIlsBaseline2020:  number;
  timestamp:           string;
}

let cache: InflationCache | null = null;

async function fetchInflationData(): Promise<InflationPayload> {
  // Return cached result if still fresh (1 hour)
  if (cache && Date.now() < cache.expiresAt) {
    return cache.data;
  }

  // Fetch CPI series from Bank of Israel
  const { data: boiData } = await axios.get(
    'https://api.boi.org.il/v1/Series/BOI.CPI/',
    { timeout: 10000, headers: { Accept: 'application/json' } }
  );

  // The BOI API returns an array of observations sorted oldest-first
  // Shape: { seriesData: [{ period: "YYYY-MM", value: number }, ...] }
  const observations: { period: string; value: number }[] =
    boiData?.seriesData ?? boiData?.data ?? [];

  if (!observations.length) {
    throw new Error('BOI CPI: no observations returned');
  }

  const latest = observations[observations.length - 1];
  const baseline = observations.find(o => o.period?.startsWith('2020-01')) ?? observations[0];

  const cpiCurrent      = Number(latest.value);
  const cpiBaseline2020 = Number(baseline.value);

  if (!cpiCurrent || !cpiBaseline2020) {
    throw new Error('BOI CPI: could not parse CPI values');
  }

  // Fetch live USD/ILS
  const rateResult = await getUsdIlsRate();

  const payload: InflationPayload = {
    cpiCurrent,
    cpiBaseline2020,
    usdIls:             rateResult.rate,
    usdIlsBaseline2020: USD_ILS_BASELINE_2020,
    timestamp:          new Date().toISOString(),
  };

  cache = { data: payload, expiresAt: Date.now() + 60 * 60 * 1000 };
  return payload;
}

// GET /api/inflation
router.get('/', async (_req: Request, res: Response) => {
  try {
    const data = await fetchInflationData();
    res.json(data);
  } catch (err) {
    logger.error('Inflation route failed', err);
    res.status(502).json({ error: 'Failed to fetch inflation data' });
  }
});

export default router;
