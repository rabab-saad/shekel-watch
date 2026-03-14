import { useEffect, useRef, useState, type ReactNode } from 'react';
import apiClient from '../lib/apiClient';

// Module-level cache so the same term is never fetched twice in a session
const cache = new Map<string, string>();

interface Props {
  term:     string;
  children: ReactNode;
}

export function TermTooltip({ term, children }: Props) {
  const [open,    setOpen]    = useState(false);
  const [text,    setText]    = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  const handleClick = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true);

    if (cache.has(term)) {
      setText(cache.get(term)!);
      return;
    }

    setLoading(true);
    try {
      const { data } = await apiClient.post<{ explanation: string }>('/explain', {
        term,
        language: 'en',
      });
      cache.set(term, data.explanation);
      setText(data.explanation);
    } catch {
      setText('Could not load explanation.');
    } finally {
      setLoading(false);
    }
  };

  // Click outside → close
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  // Escape → close
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  return (
    <span
      ref={ref}
      className="relative inline-block"
      role="button"
      tabIndex={0}
      aria-label={`Explain term: ${term}`}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleClick(); }}
    >
      <span
        className="underline decoration-dotted decoration-gray-400 cursor-help"
        onClick={handleClick}
      >
        {children}
      </span>

      {open && (
        <div
          role="tooltip"
          aria-label={`Explanation for ${term}`}
          className="absolute left-0 top-full mt-1 z-50 bg-white text-gray-900 shadow-lg rounded-lg p-3 max-w-xs text-xs leading-relaxed"
        >
          {loading ? <span className="text-gray-400">Loading…</span> : text}
        </div>
      )}
    </span>
  );
}
