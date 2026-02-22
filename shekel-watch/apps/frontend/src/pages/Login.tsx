import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { supabase } from '../lib/supabaseClient';
import { useAppStore } from '../store/useAppStore';

export function Login() {
  const { i18n } = useTranslation();
  const user = useAppStore(s => s.user);
  const isRtl = i18n.language === 'he';

  if (user) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div
        className="w-full max-w-md bg-panel border border-border rounded-2xl p-8"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <div className="text-center mb-6">
          <span className="text-4xl text-gold">₪</span>
          <h1 className="text-2xl font-bold mt-2">
            {isRtl ? 'ברוך הבא ל-Shekel-Watch' : 'Welcome to Shekel-Watch'}
          </h1>
          <p className="text-sm text-muted mt-1">
            {isRtl ? 'פלטפורמת המסחר הישראלית' : 'Israeli Market Dashboard'}
          </p>
        </div>
        <Auth
          supabaseClient={supabase}
          appearance={{
            theme: ThemeSupa,
            variables: {
              default: {
                colors: {
                  brand:        '#3b82f6',
                  brandAccent:  '#2563eb',
                  inputBackground: '#1a1d2e',
                  inputBorder:  '#2a2d3e',
                  inputText:    'white',
                },
              },
            },
          }}
          providers={['google']}
          magicLink
        />
      </div>
    </div>
  );
}
