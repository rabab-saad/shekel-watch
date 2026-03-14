import { useEffect, useState } from 'react';
import apiClient from '../lib/apiClient';

export interface HistoryBar {
  time:   string;
  open:   number;
  high:   number;
  low:    number;
  close:  number;
  volume: number;
}

export type HistoryPeriod = '1wk' | '1mo' | '3mo' | '6mo' | '1y' | '2y';

export function useStockHistory(ticker: string | null, period: HistoryPeriod = '3mo') {
  const [bars, setBars]         = useState<HistoryBar[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    let cancelled = false;

    setLoading(true);
    setError(null);

    apiClient
      .get<HistoryBar[]>(`/stocks/${encodeURIComponent(ticker)}/history`, { params: { period } })
      .then(res => { if (!cancelled) setBars(res.data); })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [ticker, period]);

  return { bars, isLoading, error };
}
