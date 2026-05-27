from app.core.config import get_settings
from app.services.ai.providers.base import AIProvider
from app.services.ai.providers.mimo import MimoProvider


def create_ai_provider() -> AIProvider:
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if provider == "mimo":
        return MimoProvider(api_key=settings.mimo_api_key, model=settings.mimo_model)

    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")

