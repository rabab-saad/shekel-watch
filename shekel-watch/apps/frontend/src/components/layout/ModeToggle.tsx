import { useTranslation } from 'react-i18next';
import { useAppStore } from '../../store/useAppStore';

export function ModeToggle() {
  const { t } = useTranslation();
  const tradingMode  = useAppStore(s => s.tradingMode);
  const setMode      = useAppStore(s => s.setTradingMode);

  const isPro = tradingMode === 'pro';

  return (
    <button
      onClick={() => setMode(isPro ? 'beginner' : 'pro')}
      title={isPro ? t('mode_simple') : t('mode_pro')}
      className={`
        flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold
        border transition-colors select-none
        ${isPro
          ? 'border-gold text-gold bg-gold/10 hover:bg-gold/20'
          : 'border-border text-muted bg-surface/50 hover:text-white hover:border-white/30'
        }
      `}
    >
      {isPro ? (
        <><span>⚡</span><span>{t('mode_pro')}</span></>
      ) : (
        <><span>🟢</span><span>{t('mode_simple')}</span></>
      )}
    </button>
  );
}
