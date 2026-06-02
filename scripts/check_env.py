from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


COMMON_REQUIRED = [
    "APP_ENV",
    "LOG_LEVEL",
    "DATABASE_URL",
    "REDIS_URL",
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_STORAGE_BUCKET",
    "AI_PROVIDER",
]

PRODUCTION_REQUIRED = [
    "CORS_ORIGINS",
    "MIMO_API_KEY",
    "NEXT_PUBLIC_APP_URL",
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
]

DEVELOPMENT_REQUIRED = [
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
]

URL_KEYS = [
    "SUPABASE_URL",
    "MIMO_BASE_URL",
    "NEXT_PUBLIC_APP_URL",
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AI Data Analysis env files.")
    parser.add_argument("--file", default=".env", help="Env file to validate.")
    parser.add_argument(
        "--profile",
        choices=["development", "production"],
        default="development",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Validate key presence and types without requiring secret values.",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"Missing env file: {path}")

    env = parse_env(path)
    required = COMMON_REQUIRED + (
        PRODUCTION_REQUIRED if args.profile == "production" else DEVELOPMENT_REQUIRED
    )
    errors: list[str] = []
    warnings: list[str] = []

    for key in required:
        value = env.get(key, "")
        if not value.strip() and not args.allow_placeholders:
            errors.append(f"{key} is required.")
        elif not value.strip():
            warnings.append(f"{key} is present but empty in template mode.")

    for key in URL_KEYS:
        value = env.get(key, "").strip()
        if value and not looks_like_url(value):
            errors.append(f"{key} must be a valid http(s) URL.")

    if "MAX_UPLOAD_SIZE_BYTES" in env:
        try:
            if int(env["MAX_UPLOAD_SIZE_BYTES"]) <= 0:
                errors.append("MAX_UPLOAD_SIZE_BYTES must be positive.")
        except ValueError:
            errors.append("MAX_UPLOAD_SIZE_BYTES must be an integer.")

    cors_origins = env.get("CORS_ORIGINS")
    if cors_origins:
        try:
            parsed = json.loads(cors_origins)
            if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                errors.append("CORS_ORIGINS must be a JSON array of strings.")
        except json.JSONDecodeError:
            errors.append('CORS_ORIGINS must be JSON, for example ["https://app.example.com"].')

    provider = env.get("AI_PROVIDER", "mimo").lower()
    if provider != "mimo":
        warnings.append(f"AI_PROVIDER={provider} is configured, but only Mimo is implemented.")

    for warning in warnings:
        print(f"warning: {warning}")
    if errors:
        for error in errors:
            print(f"error: {error}")
        raise SystemExit(1)

    print(f"env ok: {path} ({args.profile})")


def parse_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


if __name__ == "__main__":
    main()
