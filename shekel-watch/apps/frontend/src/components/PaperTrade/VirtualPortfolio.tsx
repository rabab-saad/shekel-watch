import { useEffect, useState, useCallback } from 'react';
import { supabase } from '../../lib/supabaseClient';
import apiClient from '../../lib/apiClient';
import { useAppStore } from '../../store/useAppStore';
import { Spinner } from '../ui/Spinner';

interface PortfolioRow {
  symbol:        string;
  quantity:      number;
  avg_buy_price: number;
}

interface QuoteResult {
  ticker: string;
  price:  number;
}

interface DisplayRow extends PortfolioRow {
  currentPrice: number;
  pnl:          number;
  pnlPct:       number;
}

export function VirtualPortfolio() {
  const user = useAppStore(s => s.user);
  const [rows,    setRows]    = useState<DisplayRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const { data: holdings } = await supabase
        .from('virtual_portfolio')
        .select('symbol, quantity, avg_buy_price')
        .eq('user_id', user.id);

      if (!holdings || holdings.length === 0) { setRows([]); return; }

      const tickers = holdings.map((h: PortfolioRow) => h.symbol).join(',');
      const { data: quotes } = await apiClient.get<QuoteResult[]>(`/stocks?tickers=${tickers}`);
      const priceMap = Object.fromEntries((quotes ?? []).map(q => [q.ticker, q.price]));

      setRows((holdings as PortfolioRow[]).map(h => {
        const currentPrice = priceMap[h.symbol] ?? h.avg_buy_price;
        const pnl    = (currentPrice - h.avg_buy_price) * h.quantity;
        const pnlPct = ((currentPrice - h.avg_buy_price) / h.avg_buy_price) * 100;
        return { ...h, currentPrice, pnl, pnlPct };
      }));
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Initial load + refresh on virtual_portfolio changes
  useEffect(() => {
    load();
    if (!user) return;
    const channel = supabase
      .channel(`vport-${user.id}`)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'virtual_portfolio', filter: `user_id=eq.${user.id}` }, load)
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [user, load]);

  const thClass = 'px-3 py-2 text-start text-xs font-medium text-muted uppercase tracking-wider';

  if (loading) return <Spinner />;

  return (
    <div className="bg-panel border border-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <h2 className="font-semibold text-sm">תיק נייר  |  Virtual Portfolio</h2>
      </div>

      {rows.length === 0 ? (
        <p className="px-4 py-6 text-sm text-muted text-center">אין אחזקות. קנה מניה כדי להתחיל.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface/50">
              <tr>
                <th className={thClass}>סמל</th>
                <th className={thClass}>כמות</th>
                <th className={thClass}>מחיר קנייה ₪</th>
                <th className={thClass}>מחיר נוכחי ₪</th>
                <th className={thClass}>רווח/הפסד ₪</th>
                <th className={thClass}>%</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map(r => (
                <tr key={r.symbol} className="hover:bg-white/5 transition-colors">
                  <td className="px-3 py-3 font-mono font-semibold text-accent">{r.symbol}</td>
                  <td className="px-3 py-3 font-mono">{r.quantity}</td>
                  <td className="px-3 py-3 font-mono">₪{r.avg_buy_price.toLocaleString('he-IL', { maximumFractionDigits: 2 })}</td>
                  <td className="px-3 py-3 font-mono">₪{r.currentPrice.toLocaleString('he-IL', { maximumFractionDigits: 2 })}</td>
                  <td className={`px-3 py-3 font-mono font-semibold ${r.pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                    {r.pnl >= 0 ? '+' : ''}₪{r.pnl.toLocaleString('he-IL', { maximumFractionDigits: 2 })}
                  </td>
                  <td className={`px-3 py-3 font-mono ${r.pnlPct >= 0 ? 'text-bull' : 'text-bear'}`}>
                    {r.pnlPct >= 0 ? '+' : ''}{r.pnlPct.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
