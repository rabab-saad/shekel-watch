import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Watchlist } from './pages/Watchlist';
import { Profile }      from './pages/Profile';
import { PaperTrading } from './pages/PaperTrading';
import { supabase } from './lib/supabaseClient';
import { useAppStore } from './store/useAppStore';

export default function App() {
  const setUser         = useAppStore(s => s.setUser);
  const initTradingMode = useAppStore(s => s.initTradingMode);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      if (session?.user) initTradingMode();
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session?.user) initTradingMode();
    });

    return () => subscription.unsubscribe();
  }, [setUser, initTradingMode]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<AppShell />}>
        <Route path="/"          element={<Dashboard />} />
        <Route path="/watchlist"     element={<Watchlist />} />
        <Route path="/profile"       element={<Profile />} />
        <Route path="/paper-trading" element={<PaperTrading />} />
      </Route>
    </Routes>
  );
}
