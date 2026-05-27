export function getPublicEnv() {
  return {
    apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
    supabaseKey:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  };
}
