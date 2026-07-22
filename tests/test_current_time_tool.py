"""CurrentTimeTool 参数校验与时区转换测试。"""

import unittest
from datetime import UTC, datetime

from app.tools.current_time import CurrentTimeTool


class CurrentTimeToolTestCase(unittest.TestCase):
    def test_time_is_returned_in_requested_timezone(self) -> None:
        fixed_utc = datetime(2026, 7, 22, 12, 34, 56, tzinfo=UTC)
        tool = CurrentTimeTool(
            now_provider=lambda timezone: fixed_utc.astimezone(timezone)
        )

        result = tool.execute({"timezone": "Asia/Tokyo"})

        self.assertEqual(result["timezone"], "Asia/Tokyo")
        self.assertEqual(result["datetime"], "2026-07-22T21:34:56+09:00")
        self.assertEqual(result["time"], "21:34:56")
        self.assertEqual(result["utc_offset"], "+0900")

    def test_invalid_timezone_is_rejected(self) -> None:
        tool = CurrentTimeTool()

        with self.assertRaisesRegex(ValueError, "未知的 IANA 时区"):
            tool.execute({"timezone": "Mars/Olympus"})

        with self.assertRaisesRegex(ValueError, "timezone 必须"):
            tool.execute({})


if __name__ == "__main__":
    unittest.main()
