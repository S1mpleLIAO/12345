from __future__ import annotations

import os
import yaml


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


config = Config()
