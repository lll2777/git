from functools import cached_property
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.core.config import get_settings
from app.schemas.auth import AuthUser


class SupabaseJWTVerifier:
    def __init__(self) -> None:
        self.settings = get_settings()

    @cached_property
    def issuer(self) -> str | None:
        if not self.settings.supabase_url:
            return None
        return self.settings.supabase_url.rstrip("/") + "/auth/v1"

    @cached_property
    def jwks_client(self) -> PyJWKClient | None:
        if not self.issuer:
            return None
        return PyJWKClient(f"{self.issuer}/.well-known/jwks.json")

    def verify(self, token: str) -> AuthUser:
        if self.settings.supabase_jwt_secret:
            payload = self._verify_with_legacy_secret(token)
        elif self.jwks_client:
            payload = self._verify_with_jwks(token)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase JWT verification is not configured.",
            )

        subject = payload.get("sub")
        email = payload.get("email")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token subject is missing.",
            )

        return AuthUser(
            id=subject,
            email=email,
            role=payload.get("role"),
            claims=payload,
        )

    def _verify_with_legacy_secret(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self.settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=self.settings.supabase_jwt_audience,
                issuer=self.issuer,
                options={"verify_iss": self.issuer is not None},
            )
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase access token.",
            ) from exc

    def _verify_with_jwks(self, token: str) -> dict[str, Any]:
        if not self.jwks_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase JWKS verification is not configured.",
            )

        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=self.settings.supabase_jwt_audience,
                issuer=self.issuer,
                options={"verify_iss": self.issuer is not None},
            )
        except (InvalidTokenError, PyJWKClientError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase access token.",
            ) from exc

