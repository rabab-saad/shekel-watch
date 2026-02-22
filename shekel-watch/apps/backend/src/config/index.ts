import 'dotenv/config';
import { z } from 'zod';

const envSchema = z.object({
  PORT:                      z.string().default('3001'),
  SUPABASE_URL:              z.string().url(),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
  EXCHANGE_RATE_API_KEY:     z.string().min(1),
  GEMINI_API_KEY:            z.string().min(1),
  TWILIO_ACCOUNT_SID:        z.string().min(1),
  TWILIO_AUTH_TOKEN:         z.string().min(1),
  TWILIO_WHATSAPP_FROM:      z.string().min(1),
  FRONTEND_URL:              z.string().url().default('http://localhost:5173'),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error('❌ Invalid environment variables:');
  console.error(parsed.error.flatten().fieldErrors);
  process.exit(1);
}

export const config = parsed.data;
