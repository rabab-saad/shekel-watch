import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
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
