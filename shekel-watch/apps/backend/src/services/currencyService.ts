import axios from 'axios';
import { config } from '../config';
import { logger } from '../utils/logger';

export interface RateResult {
  rate: number;
  source: string;
  fetchedAt: string;
}

export interface CurrencyRate {
  code: string;
  vsUsd: number;   // how many USD per 1 unit of this currency
  vsIls: number;   // how many ILS per 1 unit of this currency
}

export interface AllRatesResult {
  rates: CurrencyRate[];
  usdIls: number;
  fetchedAt: string;
}

const CURRENCIES = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'ILS'];

export async function getAllRates(): Promise<AllRatesResult> {
  const fetchedAt = new Date().toISOString();
  try {
    // Frankfurter: get all rates with USD as base
    const { data } = await axios.get(
      `https://api.frankfurter.app/latest?from=USD&to=${CURRENCIES.join(',')}`,
      { timeout: 6000 }
    );
    const usdIls: number = data.rates.ILS;
    const rates: CurrencyRate[] = CURRENCIES.filter(c => c !== 'ILS').map(code => {
      const usdPerCode = 1 / data.rates[code]; // e.g. 1 EUR = 1.08 USD
      return {
        code,
        vsUsd: usdPerCode,
        vsIls: usdPerCode * usdIls,
      };
    });
    return { rates, usdIls, fetchedAt };
  } catch (err) {
    logger.warn('Frankfurter multi-currency failed, falling back to exchangerate-api');
    const { data } = await axios.get(
      `https://v6.exchangerate-api.com/v6/${config.EXCHANGE_RATE_API_KEY}/latest/USD`,
      { timeout: 6000 }
    );
    const usdIls: number = data.conversion_rates.ILS;
    const rates: CurrencyRate[] = CURRENCIES.filter(c => c !== 'ILS').map(code => {
      const usdPerCode = 1 / data.conversion_rates[code];
      return {
        code,
        vsUsd: usdPerCode,
        vsIls: usdPerCode * usdIls,
      };
    });
    return { rates, usdIls, fetchedAt };
  }
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
