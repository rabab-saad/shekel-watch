import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const links = [
  { to: '/',          labelKey: 'dashboard',  icon: '📊' },
  { to: '/watchlist', labelKey: 'watchlist',  icon: '⭐' },
  { to: '/profile',   labelKey: 'profile',    icon: '⚙️' },
];

export function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="hidden md:flex flex-col w-48 min-h-[calc(100vh-3.5rem)] bg-panel border-e border-border pt-6 px-3">
      {links.map(({ to, labelKey, icon }) => (
        <NavLink
          key={to}
          to={to}
          end
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-lg text-sm mb-1 transition-colors ${
              isActive
                ? 'bg-accent/20 text-accent font-medium'
                : 'text-muted hover:text-white hover:bg-white/5'
            }`
          }
        >
          <span>{icon}</span>
          <span>{t(labelKey)}</span>
        </NavLink>
      ))}
    </aside>
  );
}
