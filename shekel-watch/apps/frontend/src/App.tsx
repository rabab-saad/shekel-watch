import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Watchlist } from './pages/Watchlist';
import { Profile } from './pages/Profile';
import { supabase } from './lib/supabaseClient';
import { useAppStore } from './store/useAppStore';

export default function App() {
  const setUser = useAppStore(s => s.setUser);

  useEffect(() => {
    // Sync auth state on mount and on change
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, [setUser]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<AppShell />}>
        <Route path="/"          element={<Dashboard />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/profile"   element={<Profile />} />
      </Route>
    </Routes>
  );
}
