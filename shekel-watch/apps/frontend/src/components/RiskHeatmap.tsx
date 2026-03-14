import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { supabase } from '../lib/supabaseClient';
import { useAppStore } from '../store/useAppStore';
import { Spinner } from './ui/Spinner';

interface WatchlistRow {
  ticker:     string;
  risk_score: number;
}

function riskMeta(score: number, t: (k: string) => string) {
  if (score <= 3) return {
    label:       t('risk_low'),
    cardClass:   'bg-green-950/60  border-green-700',
    badgeClass:  'bg-green-700/30  text-green-400',
    dotClass:    'bg-green-400',
  };
  if (score <= 6) return {
    label:       t('risk_medium'),
    cardClass:   'bg-yellow-950/60 border-yellow-700',
    badgeClass:  'bg-yellow-700/30 text-yellow-400',
    dotClass:    'bg-yellow-400',
  };
  return {
    label:       t('risk_high'),
    cardClass:   'bg-red-950/60    border-red-700',
    badgeClass:  'bg-red-700/30    text-red-400',
    dotClass:    'bg-red-400',
  };
}

export function RiskHeatmap() {
  const { t } = useTranslation();
  const user = useAppStore(s => s.user);
  const [rows,    setRows]    = useState<WatchlistRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    supabase
      .from('watchlist')
      .select('ticker, risk_score')
      .eq('user_id', user.id)
      .then(({ data }) => {
        setRows((data ?? []) as WatchlistRow[]);
        setLoading(false);
      });
  }, [user]);

  if (loading) return <Spinner />;
  if (rows.length === 0) return null;

  return (
    <div className="bg-panel border border-border rounded-xl px-5 py-4">
      <h2 className="font-semibold text-sm mb-4">
        {t('risk_heatmap')}
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {rows.map(row => {
          const score = row.risk_score ?? 0;
          const meta  = riskMeta(score, t);
          return (
            <div
              key={row.ticker}
              className={`border rounded-xl px-3 py-3 flex flex-col gap-1 ${meta.cardClass}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-sm text-white">{row.ticker}</span>
                <span className={`flex h-2 w-2 rounded-full ${meta.dotClass}`} />
              </div>
              <span className={`self-start text-xs px-2 py-0.5 rounded-full font-medium ${meta.badgeClass}`}>
                {meta.label}
              </span>
              <span className="font-mono text-xs text-muted">{t('risk_score')}: {score}/10</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
