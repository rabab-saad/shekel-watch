import { Router, Request, Response } from 'express';
import { validateGreenApi } from '../middleware/validateGreenApi';
import { sendWhatsAppMessage } from '../services/whatsappService';
import { getUsdIlsRate } from '../services/currencyService';
import { calculateArbitrageGaps } from '../services/arbitrageService';
import { generateMarketSummary } from '../services/chatgptService';
import { getBatchQuotes } from '../services/yahooFinanceService';
import { logger } from '../utils/logger';

const TASE_TICKERS = ['LUMI.TA', 'TEVA.TA', 'ESLT.TA', 'CHKP.TA', 'NICE.TA'];

const router = Router();

// POST /api/webhook/whatsapp?token=SECRET
// Green API webhook payload: https://green-api.com/en/docs/api/receiving/
router.post('/whatsapp', validateGreenApi, async (req: Request, res: Response) => {
  const { typeWebhook, senderData, messageData } = req.body;

  // Only handle incoming text messages
  if (typeWebhook !== 'incomingMessageReceived') {
    res.sendStatus(200);
    return;
  }

  const from: string = senderData?.chatId ?? '';
  const rawText: string = messageData?.textMessageData?.textMessage ?? '';
  const body = rawText.trim().toLowerCase();

  logger.info(`WhatsApp from ${from}: "${body}"`);

  // Respond 200 immediately — process async to avoid webhook retries
  res.sendStatus(200);

  try {
    let reply = '';

    if (['dollar', 'דולר', '$'].includes(body)) {
      const rate = await getUsdIlsRate();
      reply = `💵 *USD/ILS Rate*\n₪${rate.rate.toFixed(4)}\nSource: ${rate.source}\n${new Date().toLocaleString('he-IL', { timeZone: 'Asia/Jerusalem' })}`;

    } else if (['status', 'סטטוס'].includes(body)) {
      const [rate, stocks, gaps] = await Promise.all([
        getUsdIlsRate(),
        getBatchQuotes(TASE_TICKERS),
        calculateArbitrageGaps(),
      ]);
      const stockLines = stocks
        .map(s => `${s.ticker}: ${s.changePercent >= 0 ? '🟢 +' : '🔴 '}${s.changePercent.toFixed(2)}%`)
        .join('\n');
      const topGap = gaps[0];
      reply = [
        `📊 *Shekel-Watch Status*`,
        `💵 USD/ILS: ₪${rate.rate.toFixed(4)}`,
        ``,
        `*TASE Movers:*`,
        stockLines,
        ``,
        topGap
          ? `🔍 Top Gap: *${topGap.name}* ${topGap.gapPercent.toFixed(2)}%`
          : `No significant gaps detected`,
      ].join('\n');

    } else if (body === 'summary') {
      const [rate, stocks, gaps] = await Promise.all([
        getUsdIlsRate(),
        getBatchQuotes(TASE_TICKERS),
        calculateArbitrageGaps(),
      ]);
      reply = await generateMarketSummary({ rate, stocks, arbitrage: gaps, language: 'en' });

    } else if (body === 'סיכום') {
      const [rate, stocks, gaps] = await Promise.all([
        getUsdIlsRate(),
        getBatchQuotes(TASE_TICKERS),
        calculateArbitrageGaps(),
      ]);
      reply = await generateMarketSummary({ rate, stocks, arbitrage: gaps, language: 'he' });

    } else if (['help', 'עזרה'].includes(body)) {
      reply = [
        '🤖 *Shekel-Watch Commands:*',
        '• *Dollar* / *דולר* — Current USD/ILS rate',
        '• *Status* / *סטטוס* — Market overview',
        '• *Summary* — AI market summary (EN)',
        '• *סיכום* — AI market summary (HE)',
        '• *Help* / *עזרה* — This menu',
      ].join('\n');

    } else {
      reply = `Unknown command: "${rawText}"\nSend *Help* or *עזרה* for available commands.`;
    }

    await sendWhatsAppMessage(from, reply);
  } catch (err) {
    logger.error('WhatsApp handler error', err);
    try {
      await sendWhatsAppMessage(from, '⚠️ Service error. Please try again shortly.');
    } catch {
      // Swallow send error to avoid unhandled rejection
    }
  }
});

export default router;
