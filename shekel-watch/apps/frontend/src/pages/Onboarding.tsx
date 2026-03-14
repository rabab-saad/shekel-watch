import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { supabase } from '../lib/supabaseClient';
import { useAppStore } from '../store/useAppStore';

type Mode = 'beginner' | 'pro';

export function Onboarding() {
  const { t } = useTranslation();
  const navigate        = useNavigate();
  const setTradingMode  = useAppStore(s => s.setTradingMode);
  const user            = useAppStore(s => s.user);

  const [step,         setStep]         = useState<1 | 2 | 3>(1);
  const [selectedMode, setSelectedMode] = useState<Mode | null>(null);
  const [tickers,      setTickers]      = useState('');
  const [phone,        setPhone]        = useState('');
  const [whatsappOn,   setWhatsappOn]   = useState(true);
  const [submitting,   setSubmitting]   = useState(false);

  // Step 2A — upsert virtual balance, auto-advance to step 3
  useEffect(() => {
    if (step !== 2 || selectedMode !== 'beginner' || !user) return;

    const timers: ReturnType<typeof setTimeout>[] = [];

    void supabase
      .from('virtual_balance')
      .upsert({ user_id: user.id, balance_ils: 100000 }, { onConflict: 'user_id' })
      .then(() => {
        timers.push(setTimeout(() => setStep(3), 1500));
      });

    return () => timers.forEach(clearTimeout);
  }, [step, selectedMode, user]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleStep1Continue = () => {
    if (!selectedMode) return;
    setStep(2);
  };

  const handleStep2ProContinue = async () => {
    if (!user) return;

    const symbols = tickers
      .split(',')
      .map(s => s.trim().toUpperCase())
      .filter(Boolean);

    if (symbols.length > 0) {
      await supabase
        .from('watchlist')
        .insert(symbols.map(ticker => ({ user_id: user.id, ticker, market: 'NYSE' })));
    }

    setStep(3);
  };

  const handleFinish = async () => {
    if (!user || !selectedMode) return;
    setSubmitting(true);

    // Strip non-digits; remove leading 0; prepend +972
    const digits   = phone.replace(/\D/g, '');
    const local    = digits.startsWith('0') ? digits.slice(1) : digits;
    const formatted = `+972${local}`;

    await supabase
      .from('profiles')
      .update({
        trading_mode:            selectedMode,
        phone_number:            whatsappOn && local ? formatted : null,
        whatsapp_enabled:        whatsappOn && Boolean(local),
        morning_summary_enabled: whatsappOn && Boolean(local),
      })
      .eq('id', user.id);

    await setTradingMode(selectedMode);
    navigate('/');
  };

  // ── Layout ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-6">
      <div className="w-full max-w-xl">

        {/* Progress bar */}
        <div className="flex justify-center gap-2 mb-10">
          {([1, 2, 3] as const).map(s => (
            <div
              key={s}
              className={`h-2 w-10 rounded-full transition-colors duration-300 ${
                s <= step ? 'bg-accent' : 'bg-border'
              }`}
            />
          ))}
        </div>

        {/* ── STEP 1 — pick mode ─────────────────────────────────────────── */}
        {step === 1 && (
          <div className="space-y-6">
            <h1 className="text-center text-2xl font-bold text-white">
              {t('onboarding_step1_title')}
            </h1>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setSelectedMode('beginner')}
                className={`flex flex-col items-center justify-center gap-3 rounded-2xl border-2 p-6 transition-all ${
                  selectedMode === 'beginner'
                    ? 'border-green-500 bg-green-950/40'
                    : 'border-border bg-panel hover:border-green-700'
                }`}
              >
                <span className="text-5xl">🌱</span>
                <span className="font-bold text-white text-center text-sm">
                  {t('onboarding_beginner_title')}
                </span>
                <span className="text-xs text-muted text-center leading-relaxed">
                  {t('onboarding_beginner_sub')}
                </span>
              </button>

              <button
                onClick={() => setSelectedMode('pro')}
                className={`flex flex-col items-center justify-center gap-3 rounded-2xl border-2 p-6 transition-all ${
                  selectedMode === 'pro'
                    ? 'border-blue-500 bg-blue-950/40'
                    : 'border-border bg-panel hover:border-blue-700'
                }`}
              >
                <span className="text-5xl">⚡</span>
                <span className="font-bold text-white text-center text-sm">
                  {t('onboarding_pro_title')}
                </span>
                <span className="text-xs text-muted text-center leading-relaxed">
                  {t('onboarding_pro_sub')}
                </span>
              </button>
            </div>

            <button
              onClick={handleStep1Continue}
              disabled={!selectedMode}
              className="w-full py-3 rounded-xl bg-accent text-white font-semibold transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {t('onboarding_continue')}
            </button>
          </div>
        )}

        {/* ── STEP 2A — beginner: virtual balance seeded ─────────────────── */}
        {step === 2 && selectedMode === 'beginner' && (
          <div className="flex flex-col items-center gap-6 text-center py-8">
            <span className="text-7xl font-bold text-gold">₪</span>
            <h2 className="text-2xl font-bold text-white">{t('onboarding_balance_title')}</h2>
            <p className="text-muted max-w-xs leading-relaxed">{t('onboarding_balance_sub')}</p>
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin mt-2" />
          </div>
        )}

        {/* ── STEP 2B — pro: watchlist seed ──────────────────────────────── */}
        {step === 2 && selectedMode === 'pro' && (
          <div className="space-y-5">
            <h2 className="text-center text-2xl font-bold text-white">
              {t('onboarding_watchlist_title')}
            </h2>

            <textarea
              value={tickers}
              onChange={e => setTickers(e.target.value)}
              placeholder={t('onboarding_watchlist_placeholder')}
              rows={3}
              className="w-full bg-panel border border-border rounded-xl px-4 py-3 text-sm font-mono placeholder:text-muted focus:outline-none focus:border-accent resize-none"
            />
            <p className="text-xs text-muted">{t('onboarding_watchlist_hint')}</p>

            <button
              onClick={handleStep2ProContinue}
              className="w-full py-3 rounded-xl bg-accent text-white font-semibold"
            >
              {t('onboarding_continue')}
            </button>
          </div>
        )}

        {/* ── STEP 3 — WhatsApp ──────────────────────────────────────────── */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="text-center">
              <span className="text-5xl">📱</span>
              <h2 className="mt-4 text-2xl font-bold text-white">
                {t('onboarding_whatsapp_title')}
              </h2>
            </div>

            {/* Phone input */}
            <div>
              <label className="block text-xs text-muted mb-1.5">
                {t('onboarding_phone_label')}
              </label>
              <div className="flex items-center gap-2 bg-panel border border-border rounded-xl px-4 py-2.5 focus-within:border-accent transition-colors">
                <span className="text-sm text-muted font-mono select-none">+972</span>
                <div className="w-px h-4 bg-border" />
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
                  placeholder="50-000-0000"
                  className="flex-1 bg-transparent text-sm font-mono placeholder:text-muted focus:outline-none"
                />
              </div>
            </div>

            {/* Toggle */}
            <div className="flex items-center justify-between bg-panel border border-border rounded-xl px-4 py-3">
              <span className="text-sm text-white">{t('onboarding_toggle_label')}</span>
              <button
                role="switch"
                aria-checked={whatsappOn}
                onClick={() => setWhatsappOn(v => !v)}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  whatsappOn ? 'bg-accent' : 'bg-border'
                }`}
              >
                <span
                  className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow transition-transform ${
                    whatsappOn ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <button
              onClick={handleFinish}
              disabled={submitting || (whatsappOn && !phone)}
              className="w-full py-3 rounded-xl bg-accent text-white font-semibold transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {submitting ? '...' : t('onboarding_finish')}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
