import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useStocks } from '../../hooks/useStocks';
import { Badge } from '../ui/Badge';
import { Spinner } from '../ui/Spinner';

type SortKey = 'ticker' | 'price' | 'changePercent';

export function StockTable() {
  const { t } = useTranslation();
  const { stocks, isLoading } = useStocks();
  const [sortKey, setSortKey] = useState<SortKey>('changePercent');
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...stocks].sort((a, b) => {
    const va = a[sortKey];
    const vb = b[sortKey];
    if (typeof va === 'string' && typeof vb === 'string') {
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    return sortAsc ? (va as number) - (vb as number) : (vb as number) - (va as number);
  });

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(a => !a);
    else { setSortKey(key); setSortAsc(false); }
  };

  const thClass = 'px-4 py-2 text-start text-xs font-medium text-muted uppercase tracking-wider cursor-pointer hover:text-white select-none';

  return (
    <div className="bg-panel border border-border rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <h2 className="font-semibold text-sm">{t('tase_stocks')}</h2>
      </div>

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface/50">
              <tr>
                <th className={thClass} onClick={() => handleSort('ticker')}>{t('ticker')}</th>
                <th className={`${thClass} hidden sm:table-cell`}>{t('name')}</th>
                <th className={thClass} onClick={() => handleSort('price')}>{t('price')}</th>
                <th className={thClass} onClick={() => handleSort('changePercent')}>{t('change')}</th>
                <th className={`${thClass} hidden md:table-cell`}>{t('market_state')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {sorted.map(stock => (
                <tr key={stock.ticker} className="hover:bg-white/5 transition-colors">
                  <td className="px-4 py-3 font-mono font-semibold text-accent">{stock.ticker}</td>
                  <td className="px-4 py-3 text-muted hidden sm:table-cell truncate max-w-[160px]">{stock.name}</td>
                  <td className="px-4 py-3 font-mono">
                    {stock.currency === 'ILS' ? '₪' : '$'}{stock.price.toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge value={stock.changePercent} />
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      stock.marketState === 'REGULAR' ? 'text-bull' : 'text-muted'
                    }`}>
                      {stock.marketState}
                    </span>
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
