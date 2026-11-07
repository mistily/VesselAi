from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from dotenv import load_dotenv

PROVIDERS = ("anthropic", "openai", "local")


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    slack_bot_token: str
    slack_app_token: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    llm_base_url: str | None
    approver_ids: frozenset[str]
    require_separate_approver: bool
    db_path: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        if env is None:
            load_dotenv()
            env = os.environ

        provider = env.get("LLM_PROVIDER", "anthropic").strip().lower()
        if provider not in PROVIDERS:
            raise ConfigError(f"LLM_PROVIDER must be one of {PROVIDERS}, got {provider!r}")

        required = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "LLM_MODEL"]
        if provider != "local":
            required.append("LLM_API_KEY")
        missing = [k for k in required if not env.get(k, "").strip()]
        if missing:
            raise ConfigError("Missing required environment variables: " + ", ".join(missing))

        base_url = env.get("LLM_BASE_URL", "").strip() or None
        if provider == "local" and not base_url:
            raise ConfigError("LLM_BASE_URL is required when LLM_PROVIDER=local")

        approvers = frozenset(
            u.strip() for u in env.get("APPROVER_USER_IDS", "").split(",") if u.strip()
        )
        return cls(
            slack_bot_token=env["SLACK_BOT_TOKEN"].strip(),
            slack_app_token=env["SLACK_APP_TOKEN"].strip(),
            llm_provider=provider,
            llm_api_key=env.get("LLM_API_KEY", "").strip(),
            llm_model=env["LLM_MODEL"].strip(),
            llm_base_url=base_url,
            approver_ids=approvers,
            require_separate_approver=env.get("REQUIRE_SEPARATE_APPROVER", "false").strip().lower()
            in ("1", "true", "yes"),
            db_path=env.get("DB_PATH", "switch_planner.db").strip(),
        )
