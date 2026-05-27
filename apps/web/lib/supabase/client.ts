import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

import { getPublicEnv } from "@/lib/env";

let browserClient: SupabaseClient | null = null;

export function getSupabaseBrowserClient(): SupabaseClient | null {
  const env = getPublicEnv();

  if (!env.supabaseUrl || !env.supabaseKey) {
    return null;
  }

  if (!browserClient) {
    browserClient = createBrowserClient(env.supabaseUrl, env.supabaseKey);
  }

  return browserClient;
}
