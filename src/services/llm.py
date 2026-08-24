import logging

from langchain_core.language_models import BaseChatModel

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None
from langchain_openai import ChatOpenAI

from src.config import get_settings

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    """
    Get LLM with priority: OpenRouter -> OpenAI -> Gemini.

    OpenRouter dung OpenAI-compatible API (chi khac base_url).
    Uu tien OpenRouter vi dang co key trong .env.
    """
    settings = get_settings()

    providers: list[BaseChatModel] = []

    # 1. OpenRouter (uu tien cao nhat -- OpenAI-compatible)
    if settings.openrouter_api_key:
        try:
            openrouter_llm = ChatOpenAI(
                model=settings.model_name,
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=settings.llm_temperature,
                default_headers={
                    "HTTP-Referer": "https://github.com/AI20K-Build-Phase-Cohort-3/P-223",
                    "X-Title": "VF AI Onboarding Agent",
                },
            )
            providers.append(openrouter_llm)
            logger.info(f"OpenRouter LLM configured: {settings.model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenRouter LLM: {e}")

    # 2. OpenAI direct
    if settings.openai_api_key:
        try:
            openai_llm = ChatOpenAI(
                model=settings.model_name,
                api_key=settings.openai_api_key,
                temperature=settings.llm_temperature,
            )
            providers.append(openai_llm)
            logger.info(f"OpenAI LLM configured: {settings.model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}")

    # 3. Google Gemini fallback
    if settings.google_api_key and ChatGoogleGenerativeAI is not None:
        try:
            gemini_llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model_name,
                google_api_key=settings.google_api_key,
                temperature=settings.llm_temperature,
            )
            providers.append(gemini_llm)
            logger.info(f"Gemini LLM configured: {settings.gemini_model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini LLM: {e}")

    if not providers:
        raise RuntimeError(
            "No LLM provider configured. Please set OPENROUTER_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY in .env."
        )

    if len(providers) == 1:
        return providers[0]

    # Chain fallbacks: primary.with_fallbacks([fallback1, fallback2, ...])
    return providers[0].with_fallbacks(providers[1:])
