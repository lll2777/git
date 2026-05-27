import { apiFetch } from "@/lib/api/client";

export type BootstrapResponse = {
  profile: {
    id: string;
    email: string;
    display_name: string | null;
    avatar_url: string | null;
  };
  workspace: {
    id: string;
    name: string;
    slug: string;
    role: string;
  };
};

export async function bootstrapCurrentUser(accessToken: string) {
  return apiFetch<BootstrapResponse>("/api/v1/auth/bootstrap", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({}),
  });
}
