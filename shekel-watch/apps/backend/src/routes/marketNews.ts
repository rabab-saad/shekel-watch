import { Router, Request, Response } from 'express';
import { getMarketNews } from '../services/yahooFinanceService';
import { generateMarketNewsAnalysis } from '../services/chatgptService';
import { logger } from '../utils/logger';

const router = Router();

type Lang = 'en' | 'he' | 'ar';

// ── 30-minute per-language cache ─────────────────────────────────────────────
interface CacheEntry {
  data:      object;
  expiresAt: number;
}
const cache = new Map<Lang, CacheEntry>();
const TTL_MS = 30 * 60 * 1000;

// GET /api/market-news?lang=en
router.get('/', async (req: Request, res: Response) => {
  const lang: Lang = (['he', 'ar'] as Lang[]).includes(req.query.lang as Lang)
    ? (req.query.lang as Lang)
    : 'en';

  const cached = cache.get(lang);
  if (cached && Date.now() < cached.expiresAt) {
    res.json(cached.data);
    return;
  }

  // Step 1: fetch news + index quotes (non-fatal)
  let newsData: Awaited<ReturnType<typeof getMarketNews>>;
  try {
    newsData = await getMarketNews();
  } catch (err) {
    logger.warn('Market news fetch failed, proceeding with empty news', err);
    newsData = { news: [], indices: [] };
  }

  // Step 2: AI analysis (falls back to raw headlines)
  let usAnalysis     = '';
  let israelAnalysis = '';
  try {
    const result   = await generateMarketNewsAnalysis({ ...newsData, language: lang });
    usAnalysis     = result.usAnalysis;
    israelAnalysis = result.israelAnalysis;
  } catch (err) {
    logger.warn('AI market news analysis failed, falling back to headlines', err);
    const titles = newsData.news.map(n => `• ${n.title}`);
    usAnalysis     = titles.slice(0, 5).join('\n')  || 'Market data unavailable.';
    israelAnalysis = titles.slice(5, 10).join('\n') || 'Market data unavailable.';
  }

  const payload = {
    usAnalysis,
    israelAnalysis,
    indices:     newsData.indices,
    generatedAt: new Date().toISOString(),
    language:    lang,
  };

  cache.set(lang, { data: payload, expiresAt: Date.now() + TTL_MS });
  res.json(payload);
});

export default router;
