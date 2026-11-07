from ..config import Settings
from .base import BaseLLMAdapter, LLMAdapter, PlanGenerationError
from .providers import AnthropicAdapter, OpenAICompatAdapter


def build_adapter(s: Settings) -> BaseLLMAdapter:
    if s.llm_provider == "anthropic":
        return AnthropicAdapter(s.llm_api_key, s.llm_model)
    if s.llm_provider == "openai":
        return OpenAICompatAdapter(
            s.llm_api_key, s.llm_model, base_url=s.llm_base_url or "https://api.openai.com/v1"
        )
    return OpenAICompatAdapter(
        s.llm_api_key or "not-needed", s.llm_model, base_url=s.llm_base_url or "", json_mode=False
    )


__all__ = ["BaseLLMAdapter", "LLMAdapter", "PlanGenerationError", "build_adapter",
           "AnthropicAdapter", "OpenAICompatAdapter"]
