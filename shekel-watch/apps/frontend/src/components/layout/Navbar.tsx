import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { LanguageToggle } from '../ui/LanguageToggle';
import { ModeToggle } from './ModeToggle';
import { useExchangeRate } from '../../hooks/useExchangeRate';
import { useAppStore } from '../../store/useAppStore';
import { supabase } from '../../lib/supabaseClient';

export function Navbar() {
  const { t } = useTranslation();
  const { data: rate } = useExchangeRate();
  const user = useAppStore(s => s.user);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-6 h-14 bg-panel border-b border-border">
      <Link to="/" className="flex items-center gap-2 font-bold text-lg tracking-tight">
        <span className="text-gold">₪</span>
        <span>Shekel-Watch</span>
      </Link>

      {rate && (
        <div className="hidden sm:flex items-center gap-1 font-mono text-sm">
          <span className="text-muted">USD/ILS</span>
          <span className="text-white font-semibold">₪{rate.rate.toFixed(4)}</span>
        </div>
      )}

      <div className="flex items-center gap-3">
        <ModeToggle />
        <LanguageToggle />
        {user ? (
          <button
            onClick={handleSignOut}
            className="text-sm text-muted hover:text-white transition-colors"
          >
            {t('logout')}
          </button>
        ) : (
          <Link
            to="/login"
            className="px-3 py-1.5 rounded-lg bg-accent text-sm font-medium hover:bg-accent/90 transition-colors"
          >
            {t('login')}
          </Link>
        )}
      </div>
    </nav>
  );
}
