import { useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import type { User } from '@supabase/supabase-js';
import { AppShell }      from './components/layout/AppShell';
import { Dashboard }     from './pages/Dashboard';
import { Login }         from './pages/Login';
import { Watchlist }     from './pages/Watchlist';
import { Profile }       from './pages/Profile';
import { PaperTrading }  from './pages/PaperTrading';
import { Onboarding }    from './pages/Onboarding';
import { ResetPassword } from './pages/ResetPassword';
import { supabase } from './lib/supabaseClient';
import { useAppStore } from './store/useAppStore';

export default function App() {
  const setUser         = useAppStore(s => s.setUser);
  const initTradingMode = useAppStore(s => s.initTradingMode);
  const navigate        = useNavigate();

  useEffect(() => {
    const checkUser = async (user: User | null | undefined) => {
      setUser(user ?? null);
      if (!user) return;

      // Fetch trading_mode to decide whether onboarding is needed
      const { data } = await supabase
        .from('profiles')
        .select('trading_mode')
        .eq('id', user.id)
        .single();

      if (!data?.trading_mode) {
        navigate('/onboarding');
      } else {
        await initTradingMode();
      }
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      void checkUser(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'PASSWORD_RECOVERY') {
        navigate('/reset-password');
        return;
      }
      void checkUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, [setUser, initTradingMode, navigate]);

  return (
    <Routes>
      <Route path="/login"          element={<Login />} />
      <Route path="/onboarding"     element={<Onboarding />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route element={<AppShell />}>
        <Route path="/"              element={<Dashboard />} />
        <Route path="/watchlist"     element={<Watchlist />} />
        <Route path="/profile"       element={<Profile />} />
        <Route path="/paper-trading" element={<PaperTrading />} />
      </Route>
    </Routes>
  );
}
