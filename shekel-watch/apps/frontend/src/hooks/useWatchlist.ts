import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import type { WatchlistItem } from '../types';

export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchWatchlist = async () => {
    const { data, error } = await supabase
      .from('watchlist')
      .select('*')
      .order('added_at', { ascending: false });

    if (!error && data) {
      setItems(data.map(row => ({
        id:      row.id,
        ticker:  row.ticker,
        market:  row.market,
        addedAt: row.added_at,
      })));
    }
    setIsLoading(false);
  };

  const addTicker = async (ticker: string, market: 'TASE' | 'NYSE' | 'NASDAQ') => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;
    await supabase.from('watchlist').insert({ ticker, market, user_id: user.id });
    await fetchWatchlist();
  };

  const removeTicker = async (id: string) => {
    await supabase.from('watchlist').delete().eq('id', id);
    setItems(prev => prev.filter(i => i.id !== id));
  };

  useEffect(() => { fetchWatchlist(); }, []);

  return { items, isLoading, addTicker, removeTicker };
}
