import { useTranslation } from 'react-i18next';
import { DollarTicker }    from '../components/dashboard/DollarTicker';
import { StockTable }      from '../components/dashboard/StockTable';
import { ArbitragePanel }  from '../components/dashboard/ArbitragePanel';
import { MarketSummary }   from '../components/dashboard/MarketSummary';
import { WatchlistPanel }  from '../components/dashboard/WatchlistPanel';
import { RiskHeatmap }     from '../components/RiskHeatmap';
import { InflationShield } from '../components/InflationShield';
import { ErrorBoundary }   from '../components/ui/ErrorBoundary';

export function Dashboard() {
  const { t } = useTranslation();

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-white">{t('dashboard')}</h1>

      {/* Top row: rate + summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <ErrorBoundary><DollarTicker /></ErrorBoundary>
        <div className="lg:col-span-2">
          <ErrorBoundary><MarketSummary /></ErrorBoundary>
        </div>
      </div>

      {/* Middle row: stocks + arbitrage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ErrorBoundary><StockTable /></ErrorBoundary>
        </div>
        <ErrorBoundary><ArbitragePanel /></ErrorBoundary>
      </div>

      {/* Watchlist */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ErrorBoundary><WatchlistPanel /></ErrorBoundary>
      </div>

      {/* Inflation Shield */}
      <ErrorBoundary>
        <InflationShield />
      </ErrorBoundary>

      {/* Risk Heatmap */}
      <ErrorBoundary>
        <RiskHeatmap />
      </ErrorBoundary>
    </div>
  );
}
