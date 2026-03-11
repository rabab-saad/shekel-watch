import { useState, useEffect } from 'react';
import apiClient from '../lib/apiClient';

export interface CurrencyRate {
  code: string;
  vsUsd: number;
  vsIls: number;
}

export interface AllRatesResult {
  rates: CurrencyRate[];
  usdIls: number;
  fetchedAt: string;
}

export function useCurrencyRates(intervalMs = 30_000) {
  const [data, setData] = useState<AllRatesResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetch = async () => {
      try {
        const res = await apiClient.get<AllRatesResult>('/rates/all');
        if (mounted) {
          setData(res.data);
          setIsLoading(false);
        }
      } catch {
        // silently fail — ticker just won't update
      }
    };

    fetch();
    const id = setInterval(fetch, intervalMs);
    return () => { mounted = false; clearInterval(id); };
  }, [intervalMs]);

  return { data, isLoading };
}
