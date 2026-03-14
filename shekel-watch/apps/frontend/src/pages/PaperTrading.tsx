import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { VirtualBalance }  from '../components/PaperTrade/VirtualBalance';
import { BuySellPanel }    from '../components/PaperTrade/BuySellPanel';
import { VirtualPortfolio } from '../components/PaperTrade/VirtualPortfolio';

export function PaperTrading() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-white">📈 מסחר נייר  |  Paper Trading</h1>

      <ErrorBoundary>
        <VirtualBalance />
      </ErrorBoundary>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ErrorBoundary>
          <BuySellPanel />
        </ErrorBoundary>
      </div>

      <ErrorBoundary>
        <VirtualPortfolio />
      </ErrorBoundary>
    </div>
  );
}
