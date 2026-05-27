import { getPublicEnv } from "@/lib/env";

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const { apiUrl } = getPublicEnv();
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
