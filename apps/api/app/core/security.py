from functools import cached_property
from typing import Any

import httpx
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

    @cached_property
    def supabase_api_key(self) -> str | None:
        return self.settings.supabase_anon_key or self.settings.supabase_publishable_key

    async def verify(self, token: str) -> AuthUser:
        if (
            not self.settings.supabase_jwt_secret
            and not self.jwks_client
            and not self.supabase_api_key
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase JWT verification is not configured.",
            )

        try:
            payload = self._verify_with_jwks_or_secret(token)
        except HTTPException as exc:
            return await self._verify_with_supabase_auth(token, exc)

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

    def _verify_with_jwks_or_secret(self, token: str) -> dict[str, Any]:
        errors: list[Exception] = []
        if self.jwks_client:
            try:
                return self._verify_with_jwks(token)
            except HTTPException as exc:
                errors.append(exc)

        if self.settings.supabase_jwt_secret:
            try:
                return self._verify_with_legacy_secret(token)
            except HTTPException as exc:
                errors.append(exc)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase access token.",
        ) from (errors[-1] if errors else None)

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

    async def _verify_with_supabase_auth(
        self,
        token: str,
        fallback_error: HTTPException,
    ) -> AuthUser:
        if not self.settings.supabase_url or not self.supabase_api_key:
            raise fallback_error

        url = f"{self.settings.supabase_url.rstrip('/')}/auth/v1/user"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": self.supabase_api_key,
                    },
                )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth validation is temporarily unavailable.",
            ) from exc

        if response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }:
            raise fallback_error

        if response.is_error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Auth validation is temporarily unavailable.",
            )

        user = response.json()
        user_id = user.get("id")
        if not user_id:
            raise fallback_error

        claims = self._decode_unverified_claims(token)
        claims["supabase_user"] = user

        return AuthUser(
            id=user_id,
            email=user.get("email") or claims.get("email"),
            role=claims.get("role") or user.get("role"),
            claims=claims,
        )

    @staticmethod
    def _decode_unverified_claims(token: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
        except InvalidTokenError:
            return {}
        return claims if isinstance(claims, dict) else {}
