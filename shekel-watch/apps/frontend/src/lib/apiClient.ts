import axios from 'axios';

// In production (Vercel) the backend is on Railway — set VITE_BACKEND_URL.
// In development the Vite proxy forwards /api → localhost:3001 so no var needed.
const baseURL = import.meta.env.VITE_BACKEND_URL
  ? `${import.meta.env.VITE_BACKEND_URL}/api`
  : '/api';

const apiClient = axios.create({
  baseURL,
  timeout: 15000,
});

// Attach Supabase session token for protected routes
apiClient.interceptors.request.use(async (config) => {
  const { supabase } = await import('./supabaseClient');
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export default apiClient;
