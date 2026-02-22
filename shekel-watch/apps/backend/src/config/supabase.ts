import { createClient } from '@supabase/supabase-js';
import { config } from './index';

// Server-side client with service role key — bypasses RLS
export const supabase = createClient(
  config.SUPABASE_URL,
  config.SUPABASE_SERVICE_ROLE_KEY
);
