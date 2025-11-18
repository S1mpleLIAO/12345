from __future__ import annotations

from fastmcp import FastMCP

from models.types import AppealTop5Result
from services.appeal_service import get_top5_appeal_types_for_date
from utils.exceptions import BusinessError


def register_appeal_tools(mcp: FastMCP):
    @mcp.tool()
    def get_top5_appeal_types(date: str) -> AppealTop5Result:
        """
        统计指定日期(YYYY-MM-DD)的诉求类型 Top5：

        - 输入参数:
            date: '2025-01-01' 这样的日期字符串

        - 返回:
            {
              "date": "...",
              "total": 123,
              "items": [
                {"rank": 1, "appeal_type": "...", "count": 51, "ratio": 0.156},
                ...
              ]
            }
        """
        try:
            return get_top5_appeal_types_for_date(date)
        except BusinessError as e:
            raise e
