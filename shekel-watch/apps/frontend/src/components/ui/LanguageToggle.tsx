import { useTranslation } from 'react-i18next';

export function LanguageToggle() {
  const { i18n } = useTranslation();
  const isHebrew = i18n.language === 'he';

  return (
    <button
      onClick={() => i18n.changeLanguage(isHebrew ? 'en' : 'he')}
      className="px-3 py-1.5 rounded-lg border border-border text-sm font-medium hover:border-accent transition-colors"
      aria-label="Toggle language"
    >
      {isHebrew ? 'EN' : 'עב'}
    </button>
  );
}
