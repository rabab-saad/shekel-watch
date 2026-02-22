interface BadgeProps {
  value: number;
  suffix?: string;
}

export function Badge({ value, suffix = '%' }: BadgeProps) {
  const isUp = value >= 0;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-semibold ${
        isUp ? 'bg-bull/20 text-bull' : 'bg-bear/20 text-bear'
      }`}
    >
      {isUp ? '▲' : '▼'} {Math.abs(value).toFixed(2)}{suffix}
    </span>
  );
}
