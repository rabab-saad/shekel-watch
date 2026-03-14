import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TASE_HOLIDAYS, EARLY_CLOSE_DATES } from '../data/holidays';

// ── Types ─────────────────────────────────────────────────────────────────────

type Phase = 'pre_open' | 'continuous' | 'pre_close' | 'closing_auction' | 'closed';

interface PhaseConfig {
  /** Bilingual label always shown as "HE | EN" */
  biLabel: string;
  badge:   string;
}

const PHASE_CONFIG: Record<Phase, PhaseConfig> = {
  pre_open:         { biLabel: 'פרה-מסחר | Pre-Open',         badge: 'bg-yellow-100 text-yellow-800' },
  continuous:       { biLabel: 'מסחר רציף | Continuous',       badge: 'bg-green-100  text-green-800'  },
  pre_close:        { biLabel: 'פרה-סגירה | Pre-Close',        badge: 'bg-orange-100 text-orange-800' },
  closing_auction:  { biLabel: 'מכרז סגירה | Closing Auction', badge: 'bg-red-100    text-red-800'    },
  closed:           { biLabel: 'סגור | Closed',                badge: 'bg-gray-200   text-gray-600'   },
};

// ── IST time helpers ──────────────────────────────────────────────────────────

interface ISTInfo {
  dateStr:      string; // YYYY-MM-DD
  weekday:      string; // 'Sun' | 'Mon' | … | 'Sat'
  totalSeconds: number; // seconds since midnight in IST
}

function getISTInfo(): ISTInfo {
  const now = new Date();
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Jerusalem',
      year:    'numeric',
      month:   '2-digit',
      day:     '2-digit',
      weekday: 'short',
      hour:    '2-digit',
      minute:  '2-digit',
      second:  '2-digit',
      hour12:  false,
    })
      .formatToParts(now)
      .map(p => [p.type, p.value])
  );

  const dateStr = `${parts.year}-${parts.month}-${parts.day}`;
  const weekday = parts.weekday; // 'Sun', 'Mon', ...

  // hour12:false may return '24' at midnight — normalise it
  const h = parseInt(parts.hour, 10) % 24;
  const m = parseInt(parts.minute, 10);
  const s = parseInt(parts.second, 10);

  return { dateStr, weekday, totalSeconds: h * 3600 + m * 60 + s };
}

// ── Phase calculation ─────────────────────────────────────────────────────────

interface PhaseResult {
  phase:         Phase;
  secsUntilNext: number; // –1 = no transition today
  nextPhase:     Phase;
}

const PRE_OPEN_START   = 8 * 3600 + 45 * 60;  // 08:45
const CONT_START       = 10 * 3600;            // 10:00
const NORM_PRECLOSE    = 17 * 3600 + 15 * 60;  // 17:15
const NORM_CLOSING     = 17 * 3600 + 25 * 60;  // 17:25
const NORM_CLOSE       = 17 * 3600 + 30 * 60;  // 17:30
const EARLY_PRECLOSE   = 13 * 3600 + 15 * 60;  // 13:15
const EARLY_CLOSING    = 13 * 3600 + 25 * 60;  // 13:25
const EARLY_CLOSE      = 13 * 3600 + 30 * 60;  // 13:30

function computePhase(): PhaseResult {
  const { dateStr, weekday, totalSeconds } = getISTInfo();

  // Full holiday or Saturday → closed all day
  if (TASE_HOLIDAYS.includes(dateStr) || weekday === 'Sat') {
    return { phase: 'closed', secsUntilNext: -1, nextPhase: 'closed' };
  }

  const isEarlyClose = weekday === 'Fri' || EARLY_CLOSE_DATES.includes(dateStr);
  const preCloseStart = isEarlyClose ? EARLY_PRECLOSE : NORM_PRECLOSE;
  const closingStart  = isEarlyClose ? EARLY_CLOSING  : NORM_CLOSING;
  const marketClose   = isEarlyClose ? EARLY_CLOSE    : NORM_CLOSE;

  const ts = totalSeconds;

  if (ts < PRE_OPEN_START) {
    return { phase: 'closed',          secsUntilNext: PRE_OPEN_START - ts, nextPhase: 'pre_open' };
  }
  if (ts < CONT_START) {
    return { phase: 'pre_open',        secsUntilNext: CONT_START - ts,     nextPhase: 'continuous' };
  }
  if (ts < preCloseStart) {
    return { phase: 'continuous',      secsUntilNext: preCloseStart - ts,  nextPhase: 'pre_close' };
  }
  if (ts < closingStart) {
    return { phase: 'pre_close',       secsUntilNext: closingStart - ts,   nextPhase: 'closing_auction' };
  }
  if (ts <= marketClose) {
    return { phase: 'closing_auction', secsUntilNext: marketClose - ts,    nextPhase: 'closed' };
  }
  return { phase: 'closed', secsUntilNext: -1, nextPhase: 'closed' };
}

// ── Countdown formatter ───────────────────────────────────────────────────────

function formatCountdown(secs: number): string {
  if (secs <= 0) return '';
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${m}:${ss}`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function TASEPhaseTimer() {
  const { t } = useTranslation();
  const [result, setResult] = useState<PhaseResult>(computePhase);

  useEffect(() => {
    const id = setInterval(() => setResult(computePhase()), 1000);
    return () => clearInterval(id);
  }, []);

  const config  = PHASE_CONFIG[result.phase];
  const nextCfg = PHASE_CONFIG[result.nextPhase];
  const cd      = formatCountdown(result.secsUntilNext);

  return (
    <div className="hidden sm:flex items-center gap-1.5">
      {/* Phase badge */}
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap ${config.badge}`}>
        {config.biLabel}
      </span>

      {/* Countdown */}
      {cd && (
        <span className="text-xs text-muted font-mono whitespace-nowrap">
          ⏱ {cd} {t('phase_until')} {nextCfg.biLabel.split(' | ')[1]}
        </span>
      )}
    </div>
  );
}
