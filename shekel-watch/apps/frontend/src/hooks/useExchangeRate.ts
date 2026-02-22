import { useState, useEffect } from 'react';
import apiClient from '../lib/apiClient';
import type { RateResult } from '../types';

export function useExchangeRate(intervalMs = 30_000) {
  const [data, setData] = useState<RateResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchRate = async () => {
      try {
        const res = await apiClient.get<RateResult>('/rates/usd-ils');
        if (mounted) {
          setData(res.data);
          setError(null);
          setIsLoading(false);
        }
      } catch {
        if (mounted) setError('Failed to fetch rate');
      }
    };

    fetchRate();
    const id = setInterval(fetchRate, intervalMs);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return { data, isLoading, error };
}
