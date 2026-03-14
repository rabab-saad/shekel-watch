import { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabaseClient';
import { useAppStore } from '../../store/useAppStore';

export function VirtualBalance() {
  const user = useAppStore(s => s.user);
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    if (!user) return;

    // Initial fetch
    supabase
      .from('virtual_balance')
      .select('balance_ils')
      .eq('user_id', user.id)
      .single()
      .then(({ data }) => {
        if (data) setBalance(data.balance_ils);
        else setBalance(100000); // default before first trade
      });

    // Realtime subscription
    const channel = supabase
      .channel(`vbal-${user.id}`)
      .on(
        'postgres_changes',
        {
          event:  '*',
          schema: 'public',
          table:  'virtual_balance',
          filter: `user_id=eq.${user.id}`,
        },
        payload => {
          const row = payload.new as { balance_ils?: number };
          if (row?.balance_ils !== undefined) setBalance(row.balance_ils);
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [user]);

  const formatted = balance != null
    ? balance.toLocaleString('he-IL', { maximumFractionDigits: 2 })
    : '—';

  return (
    <div className="bg-panel border border-border rounded-xl px-5 py-4 flex items-center justify-between">
      <span className="text-sm text-muted">יתרה וירטואלית</span>
      <span className="font-mono font-bold text-lg text-gold">₪{formatted}</span>
    </div>
  );
}
