import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

export function AppShell() {
  const { i18n } = useTranslation();
  const isRtl = i18n.language === 'he';

  useEffect(() => {
    document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', i18n.language);
    document.documentElement.style.fontFamily = isRtl
      ? "'Heebo', sans-serif"
      : "'Inter', sans-serif";
  }, [isRtl, i18n.language]);

  return (
    <div className={`min-h-screen bg-surface text-white ${isRtl ? 'font-hebrew' : 'font-sans'}`}>
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
