import { useState, useEffect } from 'react';
import apiClient from '../lib/apiClient';
import type { ArbitrageResult } from '../types';

export function useArbitrage(intervalMs = 120_000) {
  const [gaps, setGaps] = useState<ArbitrageResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchGaps = async () => {
      try {
        const res = await apiClient.get<ArbitrageResult[]>('/arbitrage');
        if (mounted) {
          setGaps(res.data);
          setError(null);
          setIsLoading(false);
        }
      } catch {
        if (mounted) setError('Failed to fetch arbitrage data');
      }
    };

    fetchGaps();
    const id = setInterval(fetchGaps, intervalMs);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return { gaps, isLoading, error };
}
