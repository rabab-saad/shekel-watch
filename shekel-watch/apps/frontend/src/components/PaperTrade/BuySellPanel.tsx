import { useState } from 'react';
import apiClient from '../../lib/apiClient';
import type { QuoteResult } from '../../types';

export function BuySellPanel() {
  const [symbol,   setSymbol]   = useState('');
  const [quantity, setQuantity] = useState('');
  const [price,    setPrice]    = useState<number | null>(null);
  const [priceErr, setPriceErr] = useState('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [loading,  setLoading]  = useState(false);

  const estimatedCost = price != null && quantity ? price * Number(quantity) : null;

  const fetchPrice = async () => {
    if (!symbol.trim()) return;
    setPriceErr('');
    setPrice(null);
    try {
      const { data } = await apiClient.get<QuoteResult>(`/stocks/${encodeURIComponent(symbol.trim().toUpperCase())}`);
      setPrice(data.price);
    } catch {
      setPriceErr('Ticker not found');
    }
  };

  const trade = async (action: 'buy' | 'sell') => {
    if (!price || !quantity || !symbol) return;
    setLoading(true);
    setFeedback(null);
    try {
      const { data } = await apiClient.post<{ success: boolean; newBalance: number; error?: string }>(
        '/paper-trade',
        { symbol: symbol.trim().toUpperCase(), action, quantity: Number(quantity), currentPrice: price }
      );
      if (data.success) {
        setFeedback({ type: 'success', msg: `${action === 'buy' ? 'קנייה' : 'מכירה'} בוצעה! יתרה חדשה: ₪${data.newBalance.toLocaleString('he-IL', { maximumFractionDigits: 2 })}` });
        setQuantity('');
      } else {
        setFeedback({ type: 'error', msg: data.error ?? 'Trade failed' });
      }
    } catch (err: any) {
      setFeedback({ type: 'error', msg: err?.response?.data?.error ?? 'Trade failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-border rounded-xl px-5 py-4 space-y-4">
      <h2 className="font-semibold text-sm">קנה / מכור  |  Paper Trade</h2>

      <div className="flex gap-2">
        <input
          value={symbol}
          onChange={e => { setSymbol(e.target.value); setPrice(null); }}
          onBlur={fetchPrice}
          placeholder="סמל (לדוגמה AAPL)"
          className="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono placeholder:text-muted focus:outline-none focus:border-accent"
        />
        <input
          value={quantity}
          onChange={e => setQuantity(e.target.value)}
          placeholder="כמות"
          type="number"
          min="1"
          className="w-24 bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono placeholder:text-muted focus:outline-none focus:border-accent"
        />
      </div>

      {priceErr && <p className="text-xs text-bear">{priceErr}</p>}

      {price != null && (
        <div className="text-xs text-muted font-mono space-y-0.5">
          <div>מחיר נוכחי: <span className="text-white">₪{price.toLocaleString('he-IL', { maximumFractionDigits: 2 })}</span></div>
          {estimatedCost != null && (
            <div>עלות משוערת: <span className="text-white font-semibold">₪{estimatedCost.toLocaleString('he-IL', { maximumFractionDigits: 2 })}</span></div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <button
          disabled={!price || !quantity || loading}
          onClick={() => trade('buy')}
          className="flex-1 py-2 rounded-lg bg-bull text-white text-sm font-semibold disabled:opacity-40 hover:bg-bull/90 transition-colors"
        >
          קנה
        </button>
        <button
          disabled={!price || !quantity || loading}
          onClick={() => trade('sell')}
          className="flex-1 py-2 rounded-lg bg-bear text-white text-sm font-semibold disabled:opacity-40 hover:bg-bear/90 transition-colors"
        >
          מכור
        </button>
      </div>

      {feedback && (
        <p className={`text-xs ${feedback.type === 'success' ? 'text-bull' : 'text-bear'}`}>
          {feedback.msg}
        </p>
      )}
    </div>
  );
}
