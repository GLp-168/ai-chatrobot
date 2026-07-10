import os

from dotenv import load_dotenv

from app.prompts.templates import DEFAULT_SYSTEM_PROMPT

load_dotenv(override=True)


def _get_positive_int(name: str, default: int) -> int:
    """读取正整数环境变量，并在配置错误时尽早给出明确提示。"""
    raw_value = os.getenv(name, str(default))

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是整数，当前值为 {raw_value!r}") from exc

    if value < 1:
        raise ValueError(f"环境变量 {name} 必须大于 0，当前值为 {value}")

    return value


class Settings:
    """应用启动时读取的项目配置。"""

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    MODEL_NAME = os.getenv("MODEL_NAME")

    # System Prompt 可以按部署环境覆盖；默认模板仍保留在代码仓库中接受版本管理。
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT

    # 这是消息条数上限，不是假装精确的 Token 上限。真正 Token 预算将在后续演进。
    MAX_HISTORY_MESSAGES = _get_positive_int("MAX_HISTORY_MESSAGES", default=21)
