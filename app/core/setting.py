import os
from pathlib import Path

from dotenv import load_dotenv

from app.prompts.templates import DEFAULT_SYSTEM_PROMPT

load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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


def _get_non_negative_int(name: str, default: int) -> int:
    """读取允许为 0 的整数环境变量。"""
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是整数，当前值为 {raw_value!r}") from exc

    if value < 0:
        raise ValueError(f"环境变量 {name} 不能小于 0，当前值为 {value}")
    return value


def _get_project_path(name: str, default: Path) -> Path:
    """读取路径配置；相对路径始终以项目根目录为基准。"""
    configured = Path(os.getenv(name) or default).expanduser()
    if not configured.is_absolute():
        configured = PROJECT_ROOT / configured
    return configured.resolve()


class Settings:
    """应用启动时读取的项目配置。"""

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    MODEL_NAME = os.getenv("MODEL_NAME")
    MODEL_EMPTY_RESPONSE_RETRIES = _get_non_negative_int(
        "MODEL_EMPTY_RESPONSE_RETRIES",
        default=1,
    )

    # System Prompt 可以按部署环境覆盖；默认模板仍保留在代码仓库中接受版本管理。
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT

    # 这是消息条数上限，不是假装精确的 Token 上限。真正 Token 预算将在后续演进。
    MAX_HISTORY_MESSAGES = _get_positive_int("MAX_HISTORY_MESSAGES", default=21)

    # 防止模型重复请求工具形成死循环；一次工具轮次可以包含多个并列调用。
    MAX_TOOL_ROUNDS = _get_positive_int("MAX_TOOL_ROUNDS", default=3)

    # 模型不能提供文件路径；知识目录完全由服务端配置控制。
    KNOWLEDGE_DIR = _get_project_path("KNOWLEDGE_DIR", PROJECT_ROOT / "knowledge")
    KNOWLEDGE_CHUNK_SIZE = _get_positive_int("KNOWLEDGE_CHUNK_SIZE", default=800)
    KNOWLEDGE_CHUNK_OVERLAP = _get_positive_int(
        "KNOWLEDGE_CHUNK_OVERLAP",
        default=80,
    )
    KNOWLEDGE_TOP_K = _get_positive_int("KNOWLEDGE_TOP_K", default=3)
    KNOWLEDGE_MAX_TOP_K = _get_positive_int("KNOWLEDGE_MAX_TOP_K", default=5)
    KNOWLEDGE_MAX_QUERY_CHARACTERS = _get_positive_int(
        "KNOWLEDGE_MAX_QUERY_CHARACTERS",
        default=500,
    )
