export function formatRate(rate: number, decimals = 4): string {
  return rate.toFixed(decimals);
}

export function formatPercent(value: number, decimals = 2): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatIls(amount: number): string {
  return `₪${amount.toFixed(2)}`;
}
