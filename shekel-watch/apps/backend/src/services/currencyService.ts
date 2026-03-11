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

// Pairs to query: XYZ/USD gives "how many USD per 1 XYZ"
// USD/ILS gives "how many ILS per 1 USD"
const FX_PAIRS = 'EUR/USD,GBP/USD,JPY/USD,CHF/USD,CAD/USD,AUD/USD,CNY/USD,USD/ILS';

export async function getAllRates(): Promise<AllRatesResult> {
  const fetchedAt = new Date().toISOString();

  // Primary: Twelve Data real-time forex
  try {
    const { data } = await axios.get(
      `https://api.twelvedata.com/price?symbol=${FX_PAIRS}&apikey=${config.TWELVE_DATA_API_KEY}`,
      { timeout: 8000 }
    );

    // Response shape: { "EUR/USD": { price: "1.085" }, ... }
    const usdIls = parseFloat(data['USD/ILS']?.price);
    if (!usdIls) throw new Error('Missing USD/ILS from Twelve Data');

    const rates: CurrencyRate[] = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY'].map(code => {
      const vsUsd = parseFloat(data[`${code}/USD`]?.price ?? '0');
      return { code, vsUsd, vsIls: vsUsd * usdIls };
    });

    return { rates, usdIls, fetchedAt };
  } catch (err) {
    logger.warn('Twelve Data failed, falling back to Frankfurter + ExchangeRate-API');
  }

  // Fallback 1: Frankfurter (ECB data)
  try {
    const { data } = await axios.get(
      'https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,CHF,CAD,AUD,CNY,ILS',
      { timeout: 6000 }
    );
    const usdIls: number = data.rates.ILS;
    const rates: CurrencyRate[] = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY'].map(code => {
      const vsUsd = 1 / data.rates[code];
      return { code, vsUsd, vsIls: vsUsd * usdIls };
    });
    return { rates, usdIls, fetchedAt };
  } catch (err) {
    logger.warn('Frankfurter failed, falling back to ExchangeRate-API');
  }

  // Fallback 2: ExchangeRate-API
  const { data } = await axios.get(
    `https://v6.exchangerate-api.com/v6/${config.EXCHANGE_RATE_API_KEY}/latest/USD`,
    { timeout: 6000 }
  );
  const usdIls: number = data.conversion_rates.ILS;
  const rates: CurrencyRate[] = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY'].map(code => {
    const vsUsd = 1 / data.conversion_rates[code];
    return { code, vsUsd, vsIls: vsUsd * usdIls };
  });
  return { rates, usdIls, fetchedAt };
}

export async function getUsdIlsRate(): Promise<RateResult> {
  // Primary: Twelve Data
  try {
    const { data } = await axios.get(
      `https://api.twelvedata.com/price?symbol=USD/ILS&apikey=${config.TWELVE_DATA_API_KEY}`,
      { timeout: 5000 }
    );
    const rate = parseFloat(data.price);
    if (!rate) throw new Error('No price from Twelve Data');
    return { rate, source: 'twelvedata', fetchedAt: new Date().toISOString() };
  } catch {
    logger.warn('Twelve Data USD/ILS failed, falling back to Frankfurter');
  }

  // Fallback 1: Frankfurter
  try {
    const { data } = await axios.get(
      'https://api.frankfurter.app/latest?from=USD&to=ILS',
      { timeout: 5000 }
    );
    return { rate: data.rates.ILS, source: 'frankfurter', fetchedAt: new Date().toISOString() };
  } catch {
    logger.warn('Frankfurter API failed, falling back to exchangerate-api');
  }

  // Fallback 2: ExchangeRate-API
  const { data } = await axios.get(
    `https://v6.exchangerate-api.com/v6/${config.EXCHANGE_RATE_API_KEY}/pair/USD/ILS`,
    { timeout: 5000 }
  );
  return { rate: data.conversion_rate, source: 'exchangerate-api', fetchedAt: new Date().toISOString() };
}
