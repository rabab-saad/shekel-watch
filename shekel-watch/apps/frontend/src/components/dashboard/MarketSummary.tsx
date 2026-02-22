import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import apiClient from '../../lib/apiClient';

export function MarketSummary() {
  const { t, i18n } = useTranslation();
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSummary = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.get<{ summary: string }>('/summary', {
        params: { lang: i18n.language },
      });
      setSummary(res.data.summary);
    } catch {
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchSummary(); }, [i18n.language]);

  return (
    <div className="bg-panel border border-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold text-sm">{t('market_summary')}</h2>
        <button
          onClick={fetchSummary}
          disabled={isLoading}
          className="text-xs text-accent hover:text-accent/80 disabled:opacity-50"
        >
          {isLoading ? t('loading') : '↺ Refresh'}
        </button>
      </div>

      <div className="px-4 py-4">
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-4 bg-border rounded animate-pulse w-full" />
            <div className="h-4 bg-border rounded animate-pulse w-4/5" />
            <div className="h-4 bg-border rounded animate-pulse w-3/5" />
          </div>
        ) : summary ? (
          <blockquote className="text-sm leading-relaxed text-white/90 border-s-2 border-accent ps-3">
            {summary}
          </blockquote>
        ) : (
          <p className="text-sm text-muted">AI summary unavailable</p>
        )}
      </div>
    </div>
  );
}
