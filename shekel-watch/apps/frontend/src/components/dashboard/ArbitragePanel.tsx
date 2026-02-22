import { useTranslation } from 'react-i18next';
import { useArbitrage } from '../../hooks/useArbitrage';
import { Spinner } from '../ui/Spinner';

export function ArbitragePanel() {
  const { t } = useTranslation();
  const { gaps, isLoading } = useArbitrage();

  return (
    <div className="bg-panel border border-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <h2 className="font-semibold text-sm">{t('arbitrage_gaps')}</h2>
      </div>

      {isLoading ? (
        <Spinner />
      ) : gaps.length === 0 ? (
        <p className="px-4 py-6 text-center text-muted text-sm">{t('no_gaps')}</p>
      ) : (
        <div className="divide-y divide-border">
          {gaps.map(gap => {
            const absGap = Math.abs(gap.gapPercent);
            const barWidth = Math.min(absGap * 10, 100);
            const isHighlighted = absGap >= 2;

            return (
              <div key={gap.tickerTase} className={`px-4 py-3 ${isHighlighted ? 'bg-gold/5' : ''}`}>
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <span className="font-semibold text-sm">{gap.name}</span>
                    <span className="text-xs text-muted ms-2">
                      {gap.tickerTase} / {gap.tickerForeign}
                    </span>
                  </div>
                  <span className={`font-mono text-sm font-bold ${
                    gap.direction === 'TASE_PREMIUM'    ? 'text-gold'
                    : gap.direction === 'FOREIGN_PREMIUM' ? 'text-accent'
                    : 'text-muted'
                  }`}>
                    {gap.gapPercent >= 0 ? '+' : ''}{gap.gapPercent.toFixed(2)}%
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted">
                  <span>TASE: ₪{gap.tasePriceIls.toFixed(2)}</span>
                  <span>·</span>
                  <span>NYSE: ₪{gap.foreignPriceIls.toFixed(2)}</span>
                  <span>·</span>
                  <span className={`${
                    gap.direction === 'TASE_PREMIUM' ? 'text-gold' : 'text-accent'
                  }`}>
                    {gap.direction === 'TASE_PREMIUM' ? t('tase_premium')
                     : gap.direction === 'FOREIGN_PREMIUM' ? t('foreign_premium')
                     : 'Parity'}
                  </span>
                </div>
                <div className="mt-2 h-1 bg-border rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      gap.direction === 'TASE_PREMIUM' ? 'bg-gold' : 'bg-accent'
                    }`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
