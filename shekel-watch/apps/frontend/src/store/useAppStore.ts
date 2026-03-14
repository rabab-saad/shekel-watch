import { create } from 'zustand';
import type { User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabaseClient';

type TradingMode = 'beginner' | 'pro' | null;

const LS_KEY = 'tradingMode';

interface AppState {
  user: User | null;
  setUser: (user: User | null) => void;

  tradingMode: TradingMode;
  setTradingMode: (mode: TradingMode) => Promise<void>;
  initTradingMode: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  user:    null,
  setUser: (user) => set({ user }),

  tradingMode: null,

  setTradingMode: async (mode) => {
    set({ tradingMode: mode });
    if (mode) {
      localStorage.setItem(LS_KEY, mode);
    } else {
      localStorage.removeItem(LS_KEY);
    }
    const { user } = get();
    if (user) {
      await supabase
        .from('profiles')
        .update({ trading_mode: mode })
        .eq('id', user.id);
    }
  },

  initTradingMode: async () => {
    const cached = localStorage.getItem(LS_KEY) as TradingMode | null;
    if (cached === 'beginner' || cached === 'pro') {
      set({ tradingMode: cached });
      return;
    }
    const { user } = get();
    if (!user) return;
    const { data } = await supabase
      .from('profiles')
      .select('trading_mode')
      .eq('id', user.id)
      .single();
    const mode = (data?.trading_mode ?? null) as TradingMode;
    set({ tradingMode: mode });
    if (mode) localStorage.setItem(LS_KEY, mode);
  },
}));
