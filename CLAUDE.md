# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

北京市怀柔区 12345 市民热线智能报表生成系统。基于 Python/FastAPI 构建，使用 LLM（通义千问 Qwen-Plus）配合 MCP（Model Context Protocol）实现智能数据检索和报告生成，支持日报、供暖报告、紧急报告三种类型。

## 启动命令

```bash
# 主 Web 服务器（端口 8889）
python web_server.py

# MCP 服务器（需在不同终端分别启动）
python mcp_server/daily_report_mcp.py     # 端口 9001
python mcp_server/heating_report_mcp.py   # 端口 9002
python mcp_server/emergency_report_mcp.py # 端口 9003
```

## 系统架构

```
前端 (static/) → FastAPI (web_server.py:8889)
                          ↓
              报告生成器 (report/*.py)
                          ↓
              MCPClientWrapper (mcp_llm_clint.py)
                          ↓
              MCP 服务器 (9001-9003) → Services → MySQL
```

**核心流程**：用户请求 → FastAPI → 报告生成器 → LLM 决定调用哪些工具 → MCP 服务器执行工具 → Service 层查询数据库 → LLM 合成 Markdown 报告

## 代码结构

- `web_server.py` - FastAPI 入口，REST/SSE 端点，Dify 代理
- `mcp_llm_clint.py` - MCPClientWrapper 类，编排 LLM + 工具调用循环
- `mcp_server/` - FastMCP 服务器入口（每种报告类型一个）
- `tools/` - MCP 工具定义，使用 `@mcp.tool()` 装饰器
- `services/` - 业务逻辑和数据库查询
- `models/` - TypedDict 类型定义
- `db/connection.py` - MySQL 连接池（1-10 连接）
- `config/` - 数据库配置 (config.yaml) 和 Dify API 密钥 (dify_config.py)
- `static/` - 前端 HTML/CSS/JS，使用 SSE 实现流式响应

## 关键模式

### 添加新的 MCP 工具

1. 在 `services/<report>_service.py` 中定义服务函数
2. 在 `tools/<report>_tool.py` 中注册工具：
```python
@mcp.tool()
def my_tool(date: str) -> MyReturnType:
    """工具描述，供 LLM 理解用途。"""
    return service_function(date)
```

### 数据库查询

始终使用连接池模式：
```python
from db.connection import get_connection, release_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()
finally:
    release_connection(conn)
```

### 时间窗口

- **日报**：12 小时滚动窗口（中午到中午）
- **考核周期**：每月 19 日至次月 18 日
- 日期格式：全程使用 `YYYY-MM-DD` 字符串

## LLM 配置

- 模型：`qwen-plus`（阿里云 DashScope API）
- 最大工具调用轮数：10
- 最大生成 token 数：16,384
- Temperature：0（确定性输出）

## Dify 集成

后端代理层隐藏 API 密钥，前端通过 `static/js/dify_client.js` 中的 `DifyProxyClient` 调用：
- `order_recognition` - 接单识别
- `element_extraction` - 要素提取
- `dispatch_assistant` - 派单助手
- `address_recognition` - 地址识别

详见 `docs/dify_proxy_migration.md`。

## 依赖包

fastapi, uvicorn, pydantic, pymysql, fastmcp, openai, httpx, pyyaml
