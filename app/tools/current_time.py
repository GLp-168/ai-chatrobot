"""查询 IANA 时区当前时间的内置工具。"""

from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.schemas.tool import ToolDefinition


class CurrentTimeTool:
    """根据标准时区名称返回当前当地时间。"""

    name = "get_current_time"

    def __init__(
        self,
        now_provider: Callable[[ZoneInfo], datetime] | None = None,
    ) -> None:
        # 注入时钟让单元测试可以固定时间，正式运行默认使用系统当前时间。
        self._now_provider = now_provider or datetime.now

    @property
    def definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "获取指定 IANA 时区的当前日期和时间。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "IANA 时区名称，例如 Asia/Tokyo。",
                        }
                    },
                    "required": ["timezone"],
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, arguments: dict[str, Any]) -> dict[str, str]:
        """校验时区参数并返回 ISO 8601 时间信息。"""
        timezone_name = arguments.get("timezone")
        if not isinstance(timezone_name, str) or not timezone_name.strip():
            raise ValueError("timezone 必须是非空的 IANA 时区名称")

        timezone_name = timezone_name.strip()
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"未知的 IANA 时区: {timezone_name}") from exc

        current_time = self._now_provider(timezone)
        return {
            "timezone": timezone_name,
            "datetime": current_time.isoformat(timespec="seconds"),
            "date": current_time.date().isoformat(),
            "time": current_time.time().isoformat(timespec="seconds"),
            "utc_offset": current_time.strftime("%z"),
        }
