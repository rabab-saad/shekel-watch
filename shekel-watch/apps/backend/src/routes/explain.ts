import { Router, Request, Response } from 'express';
import OpenAI from 'openai';
import { config } from '../config';
import { requireAuth } from '../middleware/auth';
import { logger } from '../utils/logger';

const openai = new OpenAI({ apiKey: config.OPENAI_API_KEY });

const router = Router();

// POST /api/explain
router.post('/', requireAuth, async (req: Request, res: Response) => {
  const { term, language } = req.body as { term?: unknown; language?: unknown };

  if (!term || typeof term !== 'string') {
    res.status(400).json({ error: 'term is required' });
    return;
  }

  const sanitized = term.trim().slice(0, 50);
  if (!sanitized) {
    res.status(400).json({ error: 'term must be non-empty' });
    return;
  }

  const lang: 'en' | 'he' = language === 'he' ? 'he' : 'en';

  const prompt =
    `Explain the financial term '${sanitized}' in exactly 2 sentences.\n` +
    `Sentence 1: in Hebrew (for Israeli investors).\n` +
    `Sentence 2: in English (clear, jargon-free).\n` +
    `No preamble, no bullet points, just 2 sentences.`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
    });
    const explanation = response.choices[0].message.content ?? '';
    res.json({ term: sanitized, explanation, language: lang });
  } catch (err) {
    logger.error('explain route error', err);
    res.status(500).json({ error: 'Failed to explain term' });
  }
});

export default router;
