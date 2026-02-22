import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useWatchlist } from '../../hooks/useWatchlist';
import { Spinner } from '../ui/Spinner';
import { Link } from 'react-router-dom';

export function WatchlistPanel() {
  const { t } = useTranslation();
  const { items, isLoading } = useWatchlist();
  const [showAll, setShowAll] = useState(false);

  const displayed = showAll ? items : items.slice(0, 5);

  return (
    <div className="bg-panel border border-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold text-sm">{t('watchlist')}</h2>
        <Link to="/watchlist" className="text-xs text-accent hover:underline">
          {t('manage')} →
        </Link>
      </div>

      {isLoading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <div className="px-4 py-6 text-center">
          <p className="text-sm text-muted">{t('empty_watchlist')}</p>
          <Link to="/watchlist" className="mt-2 inline-block text-sm text-accent hover:underline">
            {t('add_ticker')}
          </Link>
        </div>
      ) : (
        <div className="divide-y divide-border">
          {displayed.map(item => (
            <div key={item.id} className="px-4 py-2 flex items-center justify-between">
              <span className="font-mono text-sm text-accent">{item.ticker}</span>
              <span className="text-xs text-muted">{item.market}</span>
            </div>
          ))}
          {items.length > 5 && (
            <button
              onClick={() => setShowAll(s => !s)}
              className="w-full px-4 py-2 text-xs text-muted hover:text-white transition-colors"
            >
              {showAll ? 'Show less' : `+${items.length - 5} more`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
