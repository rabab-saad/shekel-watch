import { useTranslation } from 'react-i18next';
import { useExchangeRate } from '../../hooks/useExchangeRate';
import { Spinner } from '../ui/Spinner';

export function DollarTicker() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useExchangeRate(30_000);

  if (isLoading) return <div className="bg-panel border border-border rounded-xl p-6"><Spinner /></div>;
  if (error || !data) return null;

  const prev = data.rate * 0.999; // Approximation if no prev close available
  const changePercent = ((data.rate - prev) / prev) * 100;
  const isUp = changePercent >= 0;

  return (
    <div className="bg-panel border border-border rounded-xl p-6 flex flex-col gap-2">
      <p className="text-muted text-sm">{t('usd_ils_rate')}</p>
      <div className={`font-mono text-4xl font-bold ${isUp ? 'text-bull' : 'text-bear'}`}>
        ₪{data.rate.toFixed(4)}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted">
          {t('source')}: {data.source}
        </span>
        <span className="text-xs text-muted">
          {new Date(data.fetchedAt).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
