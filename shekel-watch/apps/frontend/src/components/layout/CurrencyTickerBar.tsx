import { useCurrencyRates } from '../../hooks/useCurrencyRates';

const FLAG: Record<string, string> = {
  EUR: '🇪🇺', GBP: '🇬🇧', JPY: '🇯🇵', CHF: '🇨🇭',
  CAD: '🇨🇦', AUD: '🇦🇺', CNY: '🇨🇳',
};

function fmt(code: string, value: number) {
  // JPY and CNY are large numbers against USD — show more digits
  if (code === 'JPY') return value.toFixed(2);
  if (code === 'CNY') return value.toFixed(4);
  return value.toFixed(4);
}

export function CurrencyTickerBar() {
  const { data, isLoading } = useCurrencyRates(30_000);

  if (isLoading || !data) {
    return (
      <div className="h-8 bg-panel border-b border-border flex items-center px-4">
        <span className="text-xs text-muted animate-pulse">Loading rates...</span>
      </div>
    );
  }

  // Build ticker items: USD/ILS first, then all others
  const items = [
    { label: 'USD/ILS', value: `₪${data.usdIls.toFixed(4)}`, flag: '🇺🇸' },
    ...data.rates.map(r => [
      { label: `${r.code}/ILS`, value: `₪${fmt(r.code, r.vsIls)}`, flag: FLAG[r.code] ?? '' },
      { label: `${r.code}/USD`, value: `$${fmt(r.code, r.vsUsd)}`, flag: FLAG[r.code] ?? '' },
    ]).flat(),
  ];

  // Duplicate for seamless loop
  const doubled = [...items, ...items];

  return (
    <div className="h-8 bg-panel border-b border-border overflow-hidden relative flex items-center">
      <div className="flex animate-ticker whitespace-nowrap">
        {doubled.map((item, i) => (
          <span key={i} className="inline-flex items-center gap-1 px-5 text-xs font-mono">
            <span>{item.flag}</span>
            <span className="text-muted">{item.label}</span>
            <span className="text-white font-semibold">{item.value}</span>
            <span className="text-border mx-2">|</span>
          </span>
        ))}
      </div>
    </div>
  );
}
