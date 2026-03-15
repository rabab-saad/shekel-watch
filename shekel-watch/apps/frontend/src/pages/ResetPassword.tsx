import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { useTranslation } from 'react-i18next';
import { supabase } from '../lib/supabaseClient';

export function ResetPassword() {
  const { i18n } = useTranslation();
  const isRtl = i18n.language === 'he';

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div
        className="w-full max-w-md bg-panel border border-border rounded-2xl p-8"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <div className="text-center mb-6">
          <span className="text-4xl text-gold">₪</span>
          <h1 className="text-2xl font-bold mt-2">
            {isRtl ? 'איפוס סיסמה' : 'Reset Password'}
          </h1>
          <p className="text-sm text-muted mt-1">
            {isRtl ? 'הזן סיסמה חדשה' : 'Enter your new password below'}
          </p>
        </div>
        <Auth
          supabaseClient={supabase}
          view="update_password"
          appearance={{
            theme: ThemeSupa,
            variables: {
              default: {
                colors: {
                  brand:           '#3b82f6',
                  brandAccent:     '#2563eb',
                  inputBackground: '#1a1d2e',
                  inputBorder:     '#2a2d3e',
                  inputText:       'white',
                },
              },
            },
          }}
        />
      </div>
    </div>
  );
}
