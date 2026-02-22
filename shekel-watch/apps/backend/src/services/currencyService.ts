import axios from 'axios';
import { config } from '../config';
import { logger } from '../utils/logger';

export interface RateResult {
  rate: number;
  source: string;
  fetchedAt: string;
}

export async function getUsdIlsRate(): Promise<RateResult> {
  try {
    // Primary: Frankfurter (ECB data — no API key required)
    const { data } = await axios.get(
      'https://api.frankfurter.app/latest?from=USD&to=ILS',
      { timeout: 5000 }
    );
    return {
      rate: data.rates.ILS,
      source: 'frankfurter',
      fetchedAt: new Date().toISOString(),
    };
  } catch (primaryError) {
    logger.warn('Frankfurter API failed, falling back to exchangerate-api');
    // Fallback: exchangerate-api.com free tier
    const { data } = await axios.get(
      `https://v6.exchangerate-api.com/v6/${config.EXCHANGE_RATE_API_KEY}/pair/USD/ILS`,
      { timeout: 5000 }
    );
    return {
      rate: data.conversion_rate,
      source: 'exchangerate-api',
      fetchedAt: new Date().toISOString(),
    };
  }
}
