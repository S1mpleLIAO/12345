from __future__ import annotations

import os
import yaml
from typing import List


class Config:
    def __init__(self, path: str = "config/config.yaml"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        db = data.get("database", {})
        if not db:
            raise ValueError("config.yaml 中缺少 'database' 配置")

        self.host: str = db["host"]
        self.port: int = int(db["port"])
        self.user: str = db["user"]
        self.password: str = db["password"]
        self.database: str = db["name"]
        self.table: str = db["table"]
        lists = data.get("data_lists", {})

        # 获取原始列表 (List[str])，如果为空则默认为空列表
        self.raw_streets: List[str] = lists.get("streets", [])
        self.raw_units: List[str] = lists.get("units", [])

    @property
    def street_list_str(self) -> str:
        """
        将街道列表转换为字符串，用顿号分隔。
        例如："龙山街道、泉河街道、怀柔镇..."
        """
        return "、".join(self.raw_streets)

    @property
    def unit_list_str(self) -> str:
        """
        将单位列表转换为字符串，用顿号分隔。
        例如："环卫公司、怀胜公司、示范区管委会..."
        """
        return "、".join(self.raw_units)


config = Config()
