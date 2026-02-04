"""
Dify API 配置管理
存储所有 Dify API 的密钥和配置信息
"""
import os
from typing import Dict

# Dify API 基础配置
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://121.43.245.245:5001/v1")

# 各个应用的 API 密钥配置
# 生产环境应该从环境变量读取，这里提供默认值用于开发
DIFY_API_KEYS: Dict[str, str] = {
    # 接单识别助手
    "order_recognition": os.getenv("DIFY_ORDER_KEY", "app-rBYgj9vKWewVLflK64xFtDap"),

    # 需求要素提取
    "element_extraction": os.getenv("DIFY_ELEMENT_KEY", "app-UGozoIrpuwIxeGaHzNSHsKWz"),

    # 派单助手
    "dispatch_assistant": os.getenv("DIFY_DISPATCH_KEY", "app-ja847DdFKufaS29cIeAn3WKl"),

    # 地址识别
    "address_recognition": os.getenv("DIFY_ADDRESS_KEY", "app-3uKaB3kZeoUI5GAsktA61P5H"),
}

# 应用类型到密钥的映射
def get_api_key(app_type: str) -> str:
    """
    根据应用类型获取对应的 API 密钥

    Args:
        app_type: 应用类型 (order_recognition, element_extraction, etc.)

    Returns:
        对应的 API 密钥

    Raises:
        ValueError: 如果应用类型不存在
    """
    if app_type not in DIFY_API_KEYS:
        raise ValueError(f"未知的应用类型: {app_type}. 可用类型: {list(DIFY_API_KEYS.keys())}")

    return DIFY_API_KEYS[app_type]


# 用户标识配置
DIFY_DEFAULT_USER = "frontend-user"
