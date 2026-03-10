import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { supabase } from '../lib/supabaseClient';
import { useAppStore } from '../store/useAppStore';
import { Spinner } from '../components/ui/Spinner';

interface Profile {
  display_name: string | null;
  phone_number: string | null;
  whatsapp_enabled: boolean;
  language: 'en' | 'he';
}

export function Profile() {
  const { t, i18n } = useTranslation();
  const user = useAppStore(s => s.user);
  const isRtl = i18n.language === 'he';

  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [displayName, setDisplayName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [whatsappEnabled, setWhatsappEnabled] = useState(false);

  useEffect(() => {
    if (!user) return;
    supabase
      .from('profiles')
      .select('display_name, phone_number, whatsapp_enabled, language')
      .eq('id', user.id)
      .single()
      .then(({ data, error }) => {
        if (error) { setIsLoading(false); return; }
        setProfile(data);
        setDisplayName(data.display_name ?? '');
        setPhoneNumber(data.phone_number ?? '');
        setWhatsappEnabled(data.whatsapp_enabled ?? false);
        setIsLoading(false);
      });
  }, [user]);

  if (!user) return <Navigate to="/login" replace />;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSaved(false);

    // Basic phone validation: must start with + and have digits
    if (phoneNumber && !/^\+\d{7,15}$/.test(phoneNumber)) {
      setError(isRtl ? 'מספר טלפון לא תקין. פורמט: +972501234567' : 'Invalid phone number. Format: +972501234567');
      setIsSaving(false);
      return;
    }

    const { error: updateError } = await supabase
      .from('profiles')
      .update({
        display_name:     displayName || null,
        phone_number:     phoneNumber || null,
        whatsapp_enabled: phoneNumber ? whatsappEnabled : false,
      })
      .eq('id', user.id);

    if (updateError) {
      setError(updateError.message);
    } else {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
    setIsSaving(false);
  };

  if (isLoading) return <Spinner />;

  return (
    <div className="max-w-lg mx-auto space-y-6" dir={isRtl ? 'rtl' : 'ltr'}>
      <h1 className="text-xl font-bold">{isRtl ? 'הגדרות פרופיל' : 'Profile Settings'}</h1>

      <form onSubmit={handleSave} className="bg-panel border border-border rounded-xl p-6 space-y-5">

        {/* Email (read-only) */}
        <div className="space-y-1">
          <label className="text-xs text-muted uppercase tracking-wide">
            {isRtl ? 'אימייל' : 'Email'}
          </label>
          <p className="text-sm font-mono text-white/70">{user.email}</p>
        </div>

        {/* Display Name */}
        <div className="space-y-1">
          <label className="text-xs text-muted uppercase tracking-wide">
            {isRtl ? 'שם תצוגה' : 'Display Name'}
          </label>
          <input
            type="text"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            placeholder={isRtl ? 'השם שלך' : 'Your name'}
            className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
          />
        </div>

        {/* WhatsApp Section */}
        <div className="border-t border-border pt-5 space-y-4">
          <h2 className="text-sm font-semibold">
            📱 {isRtl ? 'התראות WhatsApp' : 'WhatsApp Alerts'}
          </h2>

          <div className="space-y-1">
            <label className="text-xs text-muted uppercase tracking-wide">
              {isRtl ? 'מספר טלפון (עם קידומת מדינה)' : 'Phone Number (with country code)'}
            </label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={e => setPhoneNumber(e.target.value)}
              placeholder="+972501234567"
              dir="ltr"
              className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent"
            />
            <p className="text-xs text-muted">
              {isRtl ? 'הזן מספר WhatsApp שלך כולל קידומת המדינה' : 'Enter your WhatsApp number including country code'}
            </p>
          </div>

          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={whatsappEnabled}
              onChange={e => setWhatsappEnabled(e.target.checked)}
              disabled={!phoneNumber}
              className="w-4 h-4 accent-accent"
            />
            <span className="text-sm">
              {isRtl
                ? 'קבל התראת בוקר ב-WhatsApp (ימים א׳–ה׳, 08:00)'
                : 'Receive morning market alert via WhatsApp (Mon–Fri, 08:00 IST)'}
            </span>
          </label>
        </div>

        {/* Error / Success */}
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
        {saved && (
          <p className="text-sm text-green-400">
            {isRtl ? '✓ הפרופיל נשמר בהצלחה' : '✓ Profile saved successfully'}
          </p>
        )}

        <button
          type="submit"
          disabled={isSaving}
          className="w-full py-2 bg-accent rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors disabled:opacity-50"
        >
          {isSaving
            ? (isRtl ? 'שומר...' : 'Saving...')
            : (isRtl ? 'שמור שינויים' : 'Save Changes')}
        </button>
      </form>
    </div>
  );
}
