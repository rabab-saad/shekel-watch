import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import apiClient from '../lib/apiClient';

interface InflationData {
  cpiCurrent:          number;
  cpiBaseline2020:     number;
  usdIls:              number;
  usdIlsBaseline2020:  number;
  timestamp:           string;
}

function fmt(n: number) {
  return n.toLocaleString('he-IL', { maximumFractionDigits: 2 });
}

export function InflationShield() {
  const { t } = useTranslation();
  const [data,    setData]    = useState<InflationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [amount,  setAmount]  = useState('10000');

  // Debounce ref
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [calc, setCalc] = useState<{
    realValueILS:     number;
    ilsLoss:          number;
    usdBought2020:    number;
    usdValueNowInILS: number;
    usdGainLoss:      number;
  } | null>(null);

  // Fetch inflation data once on mount
  useEffect(() => {
    apiClient
      .get<InflationData>('/inflation')
      .then(res => setData(res.data))
      .catch(() => {/* silently skip if BOI is unreachable */})
      .finally(() => setLoading(false));
  }, []);

  // Recalculate (debounced 500ms) whenever amount or data changes
  useEffect(() => {
    if (!data) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const n = parseFloat(amount);
      if (!n || n <= 0) { setCalc(null); return; }

      const realValueILS     = n / (data.cpiCurrent / data.cpiBaseline2020);
      const ilsLoss          = n - realValueILS;
      const usdBought2020    = n / data.usdIlsBaseline2020;
      const usdValueNowInILS = usdBought2020 * data.usdIls;
      const usdGainLoss      = usdValueNowInILS - n;

      setCalc({ realValueILS, ilsLoss, usdBought2020, usdValueNowInILS, usdGainLoss });
    }, 500);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [amount, data]);

  if (loading) return null;
  if (!data)   return null; // silently hide if BOI unreachable

  return (
    <div className="bg-panel border border-border rounded-xl px-5 py-4 space-y-4">
      <h2 className="font-semibold text-sm">{t('inflation_shield')}</h2>

      {/* Amount input */}
      <div className="flex items-center gap-2 max-w-xs">
        <span className="text-gold font-mono font-bold text-lg">₪</span>
        <input
          type="number"
          min="1"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          placeholder={t('ils_amount')}
          className="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono placeholder:text-muted focus:outline-none focus:border-accent"
        />
      </div>

      {calc && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

          {/* Card 1 — Cash in ILS */}
          <div className="border border-border rounded-xl px-4 py-4 space-y-2 bg-surface/40">
            <p className="text-xs font-medium text-muted">{t('cash_card_title')}</p>
            <p className="text-sm text-white">
              <span className="font-mono font-bold text-gold">₪{fmt(parseFloat(amount))}</span>
              {' '}{t('real_worth')}{' '}
              <span className="font-mono font-bold text-white">₪{fmt(calc.realValueILS)}</span>
              {' '}{t('real_pp')}
            </p>
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-bear/20 text-bear font-semibold">
              −₪{fmt(calc.ilsLoss)} {t('lost_inflation')}
            </span>
          </div>

          {/* Card 2 — If you bought USD */}
          <div className="border border-border rounded-xl px-4 py-4 space-y-2 bg-surface/40">
            <p className="text-xs font-medium text-muted">{t('usd_card_title')}</p>
            <p className="text-sm text-white">
              {t('would_bought')}{' '}
              <span className="font-mono font-bold text-accent">${fmt(calc.usdBought2020)}</span>
            </p>
            <p className="text-sm text-white">
              {t('worth_today')}{' '}
              <span className="font-mono font-bold text-white">₪{fmt(calc.usdValueNowInILS)}</span>
            </p>
            <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-semibold ${
              calc.usdGainLoss >= 0
                ? 'bg-bull/20 text-bull'
                : 'bg-bear/20 text-bear'
            }`}>
              {calc.usdGainLoss >= 0 ? '+' : ''}₪{fmt(calc.usdGainLoss)}
            </span>
          </div>

        </div>
      )}
    </div>
  );
}
