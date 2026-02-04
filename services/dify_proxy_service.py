"""
Dify API 代理服务
提供统一的 Dify API 调用接口，隐藏 API 密钥
"""
import httpx
from typing import Dict, Any, Optional, AsyncIterator
from fastapi import UploadFile

from config.dify_config import DIFY_BASE_URL, get_api_key, DIFY_DEFAULT_USER


class DifyProxyService:
    """Dify API 代理服务类"""

    def __init__(self):
        self.base_url = DIFY_BASE_URL
        self.timeout = httpx.Timeout(300.0, connect=10.0)  # 5分钟超时，连接10秒

    def _get_headers(self, app_type: str, content_type: Optional[str] = "application/json") -> Dict[str, str]:
        """
        构建请求头

        Args:
            app_type: 应用类型
            content_type: 内容类型，文件上传时为 None

        Returns:
            请求头字典
        """
        api_key = get_api_key(app_type)
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    async def upload_file(
        self,
        app_type: str,
        file: UploadFile,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传文件到 Dify

        Args:
            app_type: 应用类型
            file: 上传的文件对象
            user: 用户标识

        Returns:
            Dify API 响应

        Raises:
            httpx.HTTPStatusError: HTTP 错误
        """
        user = user or DIFY_DEFAULT_USER

        # 读取文件内容
        file_content = await file.read()

        # 准备 multipart/form-data
        files = {
            "file": (file.filename, file_content, file.content_type)
        }
        data = {
            "user": user
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/files/upload",
                headers=self._get_headers(app_type, content_type=None),
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()

    async def run_workflow(
        self,
        app_type: str,
        inputs: Dict[str, Any],
        response_mode: str = "blocking",
        user: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行工作流（非流式）

        Args:
            app_type: 应用类型
            inputs: 输入参数
            response_mode: 响应模式 ("blocking" 或 "streaming")
            user: 用户标识
            conversation_id: 会话ID（可选）

        Returns:
            Dify API 响应

        Raises:
            httpx.HTTPStatusError: HTTP 错误
        """
        user = user or DIFY_DEFAULT_USER

        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/workflows/run",
                headers=self._get_headers(app_type),
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def run_workflow_stream(
        self,
        app_type: str,
        inputs: Dict[str, Any],
        user: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """
        运行工作流（流式）

        Args:
            app_type: 应用类型
            inputs: 输入参数
            user: 用户标识
            conversation_id: 会话ID（可选）

        Yields:
            流式响应的字节数据

        Raises:
            httpx.HTTPStatusError: HTTP 错误
        """
        user = user or DIFY_DEFAULT_USER

        payload = {
            "inputs": inputs,
            "response_mode": "streaming",
            "user": user
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/workflows/run",
                headers=self._get_headers(app_type),
                json=payload
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk


# 创建全局单例
dify_proxy = DifyProxyService()
