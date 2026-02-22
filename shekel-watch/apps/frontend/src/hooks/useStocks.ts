import { useState, useEffect } from 'react';
import apiClient from '../lib/apiClient';
import type { QuoteResult } from '../types';

const DEFAULT_TICKERS = ['LUMI.TA', 'HARL.TA', 'TEVA.TA', 'ESLT.TA', 'NICE.TA', 'CHKP.TA'];

export function useStocks(tickers = DEFAULT_TICKERS, intervalMs = 60_000) {
  const [stocks, setStocks] = useState<QuoteResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchStocks = async () => {
      try {
        const res = await apiClient.get<QuoteResult[]>('/stocks', {
          params: { tickers: tickers.join(',') },
        });
        if (mounted) {
          setStocks(res.data);
          setError(null);
          setIsLoading(false);
        }
      } catch {
        if (mounted) setError('Failed to fetch stocks');
      }
    };

    fetchStocks();
    const id = setInterval(fetchStocks, intervalMs);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [tickers.join(','), intervalMs]);

  return { stocks, isLoading, error };
}
