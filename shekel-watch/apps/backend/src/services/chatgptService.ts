import OpenAI from 'openai';
import { config } from '../config';
import type { ArbitrageResult } from './arbitrageService';
import type { QuoteResult, NewsItem, IndexQuote } from './yahooFinanceService';
import type { RateResult } from './currencyService';

const openai = new OpenAI({ apiKey: config.OPENAI_API_KEY });

export interface SummaryInput {
  rate:      RateResult;
  stocks:    QuoteResult[];
  arbitrage: ArbitrageResult[];
  language:  'en' | 'he';
}

function buildPrompt(input: SummaryInput): string {
  const { rate, stocks, arbitrage, language } = input;

  const topMovers = [...stocks]
    .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
    .slice(0, 5)
    .map(s => `${s.ticker}: ${s.changePercent >= 0 ? '+' : ''}${s.changePercent.toFixed(2)}%`)
    .join(', ');

  const topGap = arbitrage[0];
  const gapInfo = topGap
    ? `Largest arbitrage gap: ${topGap.name} (${topGap.tickerTase}/${topGap.tickerForeign}) = ${topGap.gapPercent.toFixed(2)}%`
    : 'No significant arbitrage gaps detected.';

  if (language === 'he') {
    return `
אתה עוזר פיננסי ישראלי. כתוב סיכום שוק קצר ומקצועי בעברית (3-4 משפטים).
כלול את הנתונים הבאים:

שער דולר/שקל: ${rate.rate.toFixed(4)} ₪
מניות עם שינויים בולטים היום: ${topMovers}
${gapInfo}

הדגש מגמות עיקריות. אל תמציא נתונים נוספים. כתוב בגוף שלישי.
    `.trim();
  }

  return `
You are an Israeli financial assistant. Write a brief, professional market summary in English (3-4 sentences).
Include the following data:

USD/ILS rate: ₪${rate.rate.toFixed(4)}
Notable movers today: ${topMovers}
${gapInfo}

Highlight key trends. Do not invent additional data. Write in third person.
  `.trim();
}

export interface NewsAnalysisInput {
  news:     NewsItem[];
  indices:  IndexQuote[];
  language: 'en' | 'he' | 'ar';
}

export interface NewsAnalysisResult {
  usAnalysis:     string;
  israelAnalysis: string;
}

function buildNewsPrompt(input: NewsAnalysisInput): string {
  const { news, indices, language } = input;

  const usIndices = indices.filter(i => ['S&P 500', 'Nasdaq', 'Dow Jones'].includes(i.name));
  const ilIndices = indices.filter(i => ['TA-35', 'TA-125'].includes(i.name));

  const fmt = (i: IndexQuote) =>
    `${i.name}: ${i.price.toLocaleString()} (${i.changePercent >= 0 ? '+' : ''}${i.changePercent.toFixed(2)}%)`;

  const usStr = usIndices.length ? usIndices.map(fmt).join(', ') : 'unavailable';
  const ilStr = ilIndices.length ? ilIndices.map(fmt).join(', ') : 'unavailable';

  const headlines = news
    .map((n, i) => `${i + 1}. ${n.title}${n.summary ? ` — ${n.summary.slice(0, 120)}` : ''}`)
    .join('\n') || 'No headlines available.';

  if (language === 'he') {
    return `
אתה אנליסט פיננסי מקצועי. כתוב ניתוח שוק יומי בעברית — שתי פסקאות קצרות בלבד.

נתוני מדדים:
שוק אמריקאי: ${usStr.replace('unavailable', 'לא זמין')}
שוק ישראלי: ${ilStr.replace('unavailable', 'לא זמין')}

כותרות חדשות:
${headlines}

הוראות:
- פסקה ראשונה: שוק אמריקאי (2-3 משפטים) — סנטימנט, מניות בולטות, אירועים חשובים
- פסקה שנייה: שוק ישראלי (2-3 משפטים) — מגמות, מניות מובילות, גורמים משפיעים
- טון מקצועי ועובדתי, ללא הגזמה
- אל תמציא נתונים שאינם בחדשות
- החזר JSON בלבד: {"us":"...","israel":"..."}
    `.trim();
  }

  if (language === 'ar') {
    return `
أنت محلل مالي محترف. اكتب تحليل السوق اليومي بالعربية في فقرتين قصيرتين فقط.

بيانات المؤشرات:
السوق الأمريكي: ${usStr.replace('unavailable', 'غير متاح')}
السوق الإسرائيلي: ${ilStr.replace('unavailable', 'غير متاح')}

أبرز عناوين الأخبار:
${headlines}

التعليمات:
- الفقرة الأولى: السوق الأمريكي (2-3 جمل) — المشاعر العامة، الأسهم البارزة، الأحداث المهمة
- الفقرة الثانية: السوق الإسرائيلي (2-3 جمل) — الاتجاهات، الأسهم الرائدة، العوامل المؤثرة
- أسلوب مهني وموضوعي، بدون مبالغة
- لا تخترع بيانات غير موجودة في الأخبار
- أعد JSON فقط: {"us":"...","israel":"..."}
    `.trim();
  }

  return `
You are a professional financial analyst. Write a daily market analysis in English — exactly two short paragraphs.

Index data:
US markets: ${usStr}
Israeli market: ${ilStr}

Top news headlines:
${headlines}

Instructions:
- Paragraph 1: US markets (2-3 sentences) — overall sentiment, key movers, notable events
- Paragraph 2: Israeli market (2-3 sentences) — key trends, notable stocks/sectors, driving factors
- Tone: professional, factual, not sensational
- Do not invent data not present in the headlines
- Return ONLY valid JSON: {"us":"...","israel":"..."}
  `.trim();
}

export async function generateMarketNewsAnalysis(input: NewsAnalysisInput): Promise<NewsAnalysisResult> {
  const prompt = buildNewsPrompt(input);
  const response = await openai.chat.completions.create({
    model:           'gpt-4o-mini',
    messages:        [{ role: 'user', content: prompt }],
    response_format: { type: 'json_object' },
  });
  const content = response.choices[0].message.content ?? '{"us":"","israel":""}';
  const parsed  = JSON.parse(content);
  return {
    usAnalysis:     parsed.us     ?? '',
    israelAnalysis: parsed.israel ?? '',
  };
}

export async function generateMarketSummary(input: SummaryInput): Promise<string> {
  const prompt = buildPrompt(input);
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
  });
  return response.choices[0].message.content ?? '';
}
