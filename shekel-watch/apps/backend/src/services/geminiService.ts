import { GoogleGenerativeAI } from '@google/generative-ai';
import { config } from '../config';
import type { ArbitrageResult } from './arbitrageService';
import type { QuoteResult } from './yahooFinanceService';
import type { RateResult } from './currencyService';

const genAI = new GoogleGenerativeAI(config.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

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

export async function generateMarketSummary(input: SummaryInput): Promise<string> {
  const prompt = buildPrompt(input);
  const result = await model.generateContent(prompt);
  return result.response.text();
}
