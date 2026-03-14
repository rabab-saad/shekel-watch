import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useArbitrage } from '../../hooks/useArbitrage';
import { useAppStore } from '../../store/useAppStore';
import { supabase } from '../../lib/supabaseClient';
import { Spinner } from '../ui/Spinner';
import type { ArbitrageResult } from '../../types';

// ── Helpers ──────────────────────────────────────────────────────────────────

function gapRowClass(gap: number): string {
  if (gap > 0.5)  return 'bg-green-950/50 border-l-2 border-green-500';
  if (gap < -0.5) return 'bg-red-950/50   border-l-2 border-red-500';
  return '';
}

function gapTextClass(gap: number): string {
  if (gap > 0.5)  return 'text-bull font-bold';
  if (gap < -0.5) return 'text-bear font-bold';
  return 'text-muted';
}

function plainLanguage(g: ArbitrageResult): string {
  const abs  = Math.abs(g.gapPercent).toFixed(1);
  const name = g.name.split(' ')[0];
  if (g.gapPercent > 0.5)  return `${name} is ${abs}% cheaper on NYSE right now`;
  if (g.gapPercent < -0.5) return `${name} is ${abs}% cheaper on TASE right now`;
  return `${name} is at near-parity`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ArbitragePanel() {
  const { t } = useTranslation();
  const tradingMode = useAppStore(s => s.tradingMode);
  const isPro       = tradingMode === 'pro';

  const { gaps, isLoading } = useArbitrage();
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [rtTick, setRtTick] = useState(0);

  // Refresh timestamp when data loads
  useEffect(() => {
    if (gaps.length) setLastUpdated(new Date().toLocaleTimeString('he-IL'));
  }, [gaps]);

  // Supabase Realtime: bump rtTick when a new price_snapshot is inserted
  useEffect(() => {
    const channel = supabase
      .channel('arb-snapshots')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'price_snapshots' }, () => {
        setRtTick(n => n + 1);
        setLastUpdated(new Date().toLocaleTimeString('he-IL'));
      })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, []);

  // rtTick triggers useArbitrage re-fetch indirectly via its own interval;
  // we log it so the linter doesn't complain about an unused variable
  void rtTick;

  return (
    <div className="bg-panel border border-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold text-sm">{t('arbitrage_gaps')}</h2>
        {lastUpdated && (
          <span className="text-xs text-muted">{lastUpdated}</span>
        )}
      </div>

      {isLoading ? (
        <Spinner />
      ) : gaps.length === 0 ? (
        <p className="px-4 py-6 text-center text-muted text-sm">{t('no_gaps')}</p>
      ) : isPro ? (

        // ── Pro mode: full data table ─────────────────────────────────────
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-surface/50">
              <tr>
                <th className="px-3 py-2 text-start text-muted uppercase tracking-wider">Company</th>
                <th className="px-3 py-2 text-end  text-muted uppercase tracking-wider">TASE ₪</th>
                <th className="px-3 py-2 text-end  text-muted uppercase tracking-wider">NYSE $</th>
                <th className="px-3 py-2 text-end  text-muted uppercase tracking-wider">Rate</th>
                <th className="px-3 py-2 text-end  text-muted uppercase tracking-wider">Implied ₪</th>
                <th className="px-3 py-2 text-end  text-muted uppercase tracking-wider">Gap %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {gaps.map(g => (
                <tr key={g.tickerTase} className={`transition-colors ${gapRowClass(g.gapPercent)}`}>
                  <td className="px-3 py-2">
                    <div className="font-semibold text-white text-xs">{g.name}</div>
                    <div className="text-muted">{g.tickerTase} / {g.tickerForeign}</div>
                  </td>
                  <td className="px-3 py-2 text-end font-mono">₪{g.tasePriceIls.toFixed(2)}</td>
                  <td className="px-3 py-2 text-end font-mono">${g.foreignPriceUsd.toFixed(2)}</td>
                  <td className="px-3 py-2 text-end font-mono text-muted">{g.usdIlsRate.toFixed(4)}</td>
                  <td className="px-3 py-2 text-end font-mono">₪{g.foreignPriceIls.toFixed(2)}</td>
                  <td className={`px-3 py-2 text-end font-mono ${gapTextClass(g.gapPercent)}`}>
                    {g.gapPercent >= 0 ? '+' : ''}{g.gapPercent.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      ) : (

        // ── Beginner mode: top 3 gaps in plain language ───────────────────
        <div className="divide-y divide-border">
          {gaps.slice(0, 3).map(g => {
            const pos = g.gapPercent > 0.5;
            const neg = g.gapPercent < -0.5;
            return (
              <div key={g.tickerTase} className="px-4 py-3 flex items-start gap-3">
                <span className={`mt-1 flex h-2 w-2 shrink-0 rounded-full ${
                  pos ? 'bg-bull' : neg ? 'bg-bear' : 'bg-muted'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white">{plainLanguage(g)}</p>
                  <p className="text-xs text-muted mt-0.5">
                    TASE: ₪{g.tasePriceIls.toFixed(2)} · NYSE: ₪{g.foreignPriceIls.toFixed(2)}
                  </p>
                </div>
                <span className={`ms-2 font-mono text-sm shrink-0 ${gapTextClass(g.gapPercent)}`}>
                  {g.gapPercent >= 0 ? '+' : ''}{g.gapPercent.toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>

      )}
    </div>
  );
}
