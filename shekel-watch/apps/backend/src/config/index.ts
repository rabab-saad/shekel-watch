import 'dotenv/config';
import { z } from 'zod';

const envSchema = z.object({
  PORT:                      z.string().default('3001'),
  SUPABASE_URL:              z.string().url(),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1),
  EXCHANGE_RATE_API_KEY:     z.string().min(1),
  OPENAI_API_KEY:            z.string().min(1),
  GREENAPI_INSTANCE_ID:      z.string().min(1),
  GREENAPI_TOKEN:            z.string().min(1),
  GREENAPI_WEBHOOK_TOKEN:    z.string().min(1),
  FRONTEND_URL:              z.string().url().default('http://localhost:5173'),
});

console.log('ENV KEYS PRESENT:', Object.keys(process.env).filter(k =>
  ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','EXCHANGE_RATE_API_KEY',
   'OPENAI_API_KEY','GREENAPI_INSTANCE_ID','GREENAPI_TOKEN',
   'GREENAPI_WEBHOOK_TOKEN','FRONTEND_URL'].includes(k)
));

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error('❌ Invalid environment variables:');
  console.error(JSON.stringify(parsed.error.flatten().fieldErrors, null, 2));
  console.error('MISSING FIELDS:', Object.keys(parsed.error.flatten().fieldErrors));
  throw new Error('Missing or invalid environment variables — check Railway Variables tab');
}

export const config = parsed.data;
