# STEP 3 Authentication

## Design Intent

Authentication is implemented as a real SaaS security boundary, not a UI-only
login screen. Supabase owns identity and session issuance. The FastAPI backend
does not trust frontend state; it verifies every protected request using the
Supabase access token from the `Authorization: Bearer` header.

The design keeps auth concerns isolated:

- Frontend auth state lives in `AuthProvider`.
- Supabase browser/server clients live in `lib/supabase`.
- Backend JWT verification lives in `core/security.py`.
- Backend routes receive a normalized `AuthUser`.
- Profile and workspace persistence goes through service and repository layers.

## Frontend

Added:

- Supabase browser client.
- Supabase server client for auth callback handling.
- Next Proxy for session cookie refresh.
- Global `AuthProvider`.
- React Query provider.
- Sonner toast provider.
- `/login`
- `/register`
- `/auth/callback`
- Homepage sign-in and account creation actions.

The login/register forms include:

- Loading state.
- Disabled state when Supabase env vars are missing.
- Toast success and error handling.
- Non-blocking workspace bootstrap after successful Supabase auth.

If backend database bootstrap fails, the user remains authenticated and sees a
warning toast. That keeps identity separate from workspace initialization.

## Backend

Added:

- `GET /api/v1/auth/me`
- `POST /api/v1/auth/bootstrap`
- `AuthUser` schema.
- Supabase JWT verifier.
- Profile/workspace bootstrap service.
- Repository layer for `profiles`, `workspaces`, and `workspace_members`.
- PostgreSQL auth migration in `infra/postgres/001_auth.sql`.

JWT verification order:

1. If `SUPABASE_JWT_SECRET` is configured, verify legacy HS256 tokens.
2. Otherwise, use Supabase JWKS from:
   `SUPABASE_URL/auth/v1/.well-known/jwks.json`

Business routes should depend on `get_current_user`; they should not decode JWTs
directly.

## Environment Variables

Frontend:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

Backend:

```dotenv
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_ANON_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_JWT_AUDIENCE=authenticated
```

`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` is preferred. `NEXT_PUBLIC_SUPABASE_ANON_KEY`
is still supported for compatibility.

## API Contract

### `GET /api/v1/auth/me`

Requires:

```http
Authorization: Bearer <supabase-access-token>
```

Returns:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "authenticated",
    "claims": {}
  },
  "profile": null,
  "workspaces": []
}
```

### `POST /api/v1/auth/bootstrap`

Requires:

```http
Authorization: Bearer <supabase-access-token>
Content-Type: application/json
```

Body:

```json
{
  "display_name": "Optional name",
  "workspace_name": "Optional workspace name"
}
```

Creates or reuses:

- `profiles`
- `workspaces`
- `workspace_members`

## Database Migration

Run the SQL in `infra/postgres/001_auth.sql` against PostgreSQL before using
bootstrap in a real Supabase-connected environment.

## Validation

Local validation can run without Supabase credentials:

- `/login` and `/register` render with a clear configuration empty state.
- Frontend build and lint pass.
- Backend health check still passes.
- Auth routes are importable and return 403/401/503 depending on missing credentials
  and configuration.

Full sign-in validation requires real Supabase project values in `.env`.

## Next Step

STEP 4 is file upload:

- Dataset upload session endpoint.
- Supabase Storage signed upload flow.
- Frontend CSV upload UI.
- Dataset metadata persistence.
- Upload progress, loading, empty, and error states.
