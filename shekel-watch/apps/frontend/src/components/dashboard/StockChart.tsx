import { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  LineSeries,
  AreaSeries,
  HistogramSeries,
  type IChartApi,
} from 'lightweight-charts';
import { useAppStore } from '../../store/useAppStore';
import { useStockHistory, type HistoryPeriod } from '../../hooks/useStockHistory';
import { Spinner } from '../ui/Spinner';
import { TermTooltip } from '../TermTooltip';

// ── Indicator math ──────────────────────────────────────────────────────────

function calcRSI(closes: number[], period = 14): number[] {
  if (closes.length < period + 1) return [];
  let avgG = 0, avgL = 0;
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1];
    if (d >= 0) avgG += d; else avgL -= d;
  }
  avgG /= period;
  avgL /= period;
  const out: number[] = [];
  for (let i = period; i < closes.length; i++) {
    if (i > period) {
      const d = closes[i] - closes[i - 1];
      avgG = (avgG * (period - 1) + Math.max(d, 0)) / period;
      avgL = (avgL * (period - 1) + Math.max(-d, 0)) / period;
    }
    out.push(avgL === 0 ? 100 : 100 - 100 / (1 + avgG / avgL));
  }
  return out;
}

function ema(values: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const out: number[] = [];
  let prev: number | null = null;
  for (const v of values) {
    if (prev === null) { prev = v; out.push(v); }
    else { prev = v * k + prev * (1 - k); out.push(prev); }
  }
  return out;
}

interface MACDPoint { macd: number; signal: number; hist: number }

function calcMACD(closes: number[], fast = 12, slow = 26, sig = 9): MACDPoint[] {
  if (closes.length < slow + sig) return [];
  const fastE  = ema(closes, fast);
  const slowE  = ema(closes, slow);
  const macdL  = fastE.slice(slow - 1).map((v, i) => v - slowE[slow - 1 + i]);
  const sigL   = ema(macdL, sig);
  return macdL.slice(sig - 1).map((m, i) => ({ macd: m, signal: sigL[sig - 1 + i], hist: m - sigL[sig - 1 + i] }));
}

// ── Theme ────────────────────────────────────────────────────────────────────

const T = {
  bg:     '#0f1117',
  border: '#1e2230',
  text:   '#94a3b8',
  grid:   '#1e2230',
  up:     '#22c55e',
  down:   '#ef4444',
  area:   '#3b82f6',
  rsi:    '#a78bfa',
  macd:   '#38bdf8',
  signal: '#f59e0b',
};

function makeChartOpts(w: number, h: number) {
  return {
    width:  w,
    height: h,
    layout:    { background: { type: ColorType.Solid, color: T.bg }, textColor: T.text },
    grid:      { vertLines: { color: T.grid }, horzLines: { color: T.grid } },
    crosshair: { mode: CrosshairMode.Normal },
    rightPriceScale: { borderColor: T.border },
    timeScale:       { borderColor: T.border, timeVisible: true },
  };
}

// ── Component ────────────────────────────────────────────────────────────────

interface Props {
  ticker: string;
  period?: HistoryPeriod;
}

export function StockChart({ ticker, period = '3mo' }: Props) {
  const tradingMode = useAppStore(s => s.tradingMode);
  const isPro       = tradingMode === 'pro';
  const { bars, isLoading, error } = useStockHistory(ticker, period);

  const containerRef = useRef<HTMLDivElement>(null);
  // Keep references to all charts for cleanup
  const chartsRef = useRef<IChartApi[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || bars.length === 0) return;

    // Clean up previous charts
    chartsRef.current.forEach(c => c.remove());
    chartsRef.current = [];
    container.innerHTML = '';

    const w = container.clientWidth;
    const closes = bars.map(b => b.close);

    if (isPro) {
      // ── Pro mode: Candlestick + RSI + MACD ──────────────────────────────
      const mainH = Math.max(220, Math.round(w * 0.35));
      const indH  = 80;
      container.style.height = `${mainH + indH * 2}px`;

      // Main chart
      const mainEl = document.createElement('div');
      mainEl.style.cssText = `width:100%;height:${mainH}px`;
      container.appendChild(mainEl);

      const mainChart = createChart(mainEl, makeChartOpts(w, mainH));
      chartsRef.current.push(mainChart);

      const candle = mainChart.addSeries(CandlestickSeries, {
        upColor:         T.up,
        downColor:       T.down,
        borderUpColor:   T.up,
        borderDownColor: T.down,
        wickUpColor:     T.up,
        wickDownColor:   T.down,
      });
      candle.setData(bars.map(b => ({ time: b.time as any, open: b.open, high: b.high, low: b.low, close: b.close })));

      // RSI
      const rsiEl = document.createElement('div');
      rsiEl.style.cssText = `width:100%;height:${indH}px`;
      container.appendChild(rsiEl);

      const rsiChart = createChart(rsiEl, makeChartOpts(w, indH));
      chartsRef.current.push(rsiChart);

      const rsiVals   = calcRSI(closes, 14);
      const rsiOffset = closes.length - rsiVals.length;
      const rsiLine   = rsiChart.addSeries(LineSeries, { color: T.rsi, lineWidth: 1 });
      rsiLine.setData(rsiVals.map((v, i) => ({ time: bars[rsiOffset + i].time as any, value: v })));

      // MACD
      const macdEl = document.createElement('div');
      macdEl.style.cssText = `width:100%;height:${indH}px`;
      container.appendChild(macdEl);

      const macdChart  = createChart(macdEl, makeChartOpts(w, indH));
      chartsRef.current.push(macdChart);

      const macdData   = calcMACD(closes);
      const macdOffset = closes.length - macdData.length;

      const histLine = macdChart.addSeries(HistogramSeries, {});
      histLine.setData(macdData.map((p, i) => ({
        time:  bars[macdOffset + i].time as any,
        value: p.hist,
        color: p.hist >= 0 ? T.up : T.down,
      })));

      const macdLine   = macdChart.addSeries(LineSeries, { color: T.macd,   lineWidth: 1 });
      const signalLine = macdChart.addSeries(LineSeries, { color: T.signal, lineWidth: 1 });
      macdLine.setData(macdData.map((p, i)   => ({ time: bars[macdOffset + i].time as any, value: p.macd })));
      signalLine.setData(macdData.map((p, i) => ({ time: bars[macdOffset + i].time as any, value: p.signal })));

      // Sync time scales across all 3 charts
      const allCharts = [mainChart, rsiChart, macdChart];
      allCharts.forEach((src, si) => {
        src.timeScale().subscribeVisibleLogicalRangeChange(range => {
          if (!range) return;
          allCharts.forEach((dst, di) => { if (di !== si) dst.timeScale().setVisibleLogicalRange(range); });
        });
      });

      mainChart.timeScale().fitContent();

    } else {
      // ── Beginner mode: Area series ───────────────────────────────────────
      const h = Math.max(200, Math.round(w * 0.38));
      container.style.height = `${h}px`;

      const chart = createChart(container, makeChartOpts(w, h));
      chartsRef.current.push(chart);

      const area = chart.addSeries(AreaSeries, {
        lineColor:   T.area,
        topColor:    `${T.area}40`,
        bottomColor: `${T.area}00`,
        lineWidth:   2,
      });
      area.setData(bars.map(b => ({ time: b.time as any, value: b.close })));
      chart.timeScale().fitContent();
    }

    return () => {
      chartsRef.current.forEach(c => c.remove());
      chartsRef.current = [];
      container.innerHTML = '';
    };
  }, [bars, isPro]);

  // Resize observer — resize only the first (main) chart; panels are fixed height
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const ro = new ResizeObserver(() => {
      chartsRef.current.forEach(c => {
        c.applyOptions({ width: container.clientWidth });
      });
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  if (isLoading) return <div className="py-6"><Spinner /></div>;
  if (error)     return <p className="text-sm text-muted py-4">Failed to load chart data.</p>;
  if (!bars.length) return <p className="text-sm text-muted py-4">No history available.</p>;

  return (
    <>
      {isPro && (
        <div className="flex gap-3 text-xs text-muted mb-1 px-1">
          <TermTooltip term="RSI">RSI (14)</TermTooltip>
          <span className="opacity-40">·</span>
          <TermTooltip term="MACD">MACD (12,26,9)</TermTooltip>
        </div>
      )}
      <div ref={containerRef} className="w-full" />
    </>
  );
}
