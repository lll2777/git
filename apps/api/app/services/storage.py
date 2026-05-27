from urllib.parse import quote

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


class SupabaseStorageClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def download_object(self, *, bucket: str, path: str) -> bytes:
        if not self.settings.supabase_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase URL is not configured.",
            )

        token = (
            self.settings.supabase_service_role_key
            or self.settings.supabase_secret_key
            or self.settings.supabase_anon_key
            or self.settings.supabase_publishable_key
        )
        if not token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Storage credentials are not configured.",
            )

        encoded_path = quote(path, safe="/")
        url = f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{encoded_path}"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": token,
                },
            )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded file was not found in Supabase Storage.",
            )

        if response.is_error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to download uploaded file from Supabase Storage.",
            )

        return response.content
