import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate } from 'react-router-dom';
import { useWatchlist } from '../hooks/useWatchlist';
import { useAppStore } from '../store/useAppStore';
import { Spinner } from '../components/ui/Spinner';

export function Watchlist() {
  const { t } = useTranslation();
  const user = useAppStore(s => s.user);
  const { items, isLoading, addTicker, removeTicker } = useWatchlist();
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState<'TASE' | 'NYSE' | 'NASDAQ'>('TASE');

  if (!user) return <Navigate to="/login" replace />;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const clean = ticker.trim().toUpperCase();
    if (!clean) return;
    await addTicker(clean, market);
    setTicker('');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-xl font-bold">{t('watchlist')}</h1>

      {/* Add ticker form */}
      <form onSubmit={handleAdd} className="bg-panel border border-border rounded-xl p-4 flex gap-3 flex-wrap">
        <input
          type="text"
          value={ticker}
          onChange={e => setTicker(e.target.value)}
          placeholder={t('ticker_placeholder')}
          className="flex-1 min-w-0 bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent"
        />
        <select
          value={market}
          onChange={e => setMarket(e.target.value as typeof market)}
          className="bg-surface border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
        >
          <option value="TASE">TASE</option>
          <option value="NYSE">NYSE</option>
          <option value="NASDAQ">NASDAQ</option>
        </select>
        <button
          type="submit"
          className="px-4 py-2 bg-accent rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors"
        >
          {t('add_ticker')}
        </button>
      </form>

      {/* List */}
      <div className="bg-panel border border-border rounded-xl overflow-hidden">
        {isLoading ? (
          <Spinner />
        ) : items.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-muted">{t('empty_watchlist')}</p>
        ) : (
          <div className="divide-y divide-border">
            {items.map(item => (
              <div key={item.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="font-mono font-semibold text-accent">{item.ticker}</span>
                  <span className="text-xs text-muted ms-2">{item.market}</span>
                </div>
                <button
                  onClick={() => removeTicker(item.id)}
                  className="text-xs text-bear hover:text-bear/80 transition-colors"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
