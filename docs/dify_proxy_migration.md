# Dify API 代理层迁移指南

## 概述

本文档说明如何将前端代码从直接调用 Dify API 迁移到使用后端代理层。

## 架构变更

### 之前（不安全）
```
前端 JavaScript → 直接调用 Dify API (暴露 API 密钥)
```

### 之后（安全）
```
前端 JavaScript → 后端代理 API → Dify API (密钥隐藏在后端)
```

## 配置说明

### 1. 后端配置

API 密钥存储在 `config/dify_config.py` 中：

```python
DIFY_API_KEYS = {
    "order_recognition": "app-xxx",      # 接单识别
    "element_extraction": "app-yyy",     # 要素提取
    "dispatch_assistant": "app-zzz",     # 派单助手
    "address_recognition": "app-www",    # 地址识别
}
```

**生产环境建议**：使用环境变量
```bash
export DIFY_ORDER_KEY="app-xxx"
export DIFY_ELEMENT_KEY="app-yyy"
export DIFY_DISPATCH_KEY="app-zzz"
export DIFY_ADDRESS_KEY="app-www"
```

### 2. 前端配置

在 `index.html` 中引入客户端库：
```html
<script src="/static/js/dify_client.js"></script>
```

## 迁移步骤

### 步骤 1: 移除旧配置

**之前：**
```javascript
const DIFY_CONFIG = {
  apiKey: "app-rBYgj9vKWewVLflK64xFtDap",  // ❌ 暴露密钥
  baseUrl: "http://121.43.245.245:5001/v1",
  user: "frontend-user"
};
```

**之后：**
```javascript
const APP_TYPE = "order_recognition";  // ✅ 只需指定应用类型
const USER_ID = "frontend-order-user";
```

### 步骤 2: 文件上传迁移

**之前：**
```javascript
const formData = new FormData();
formData.append("file", file);
formData.append("user", DIFY_CONFIG.user);

const response = await fetch(`${DIFY_CONFIG.baseUrl}/files/upload`, {
  method: "POST",
  headers: { Authorization: `Bearer ${DIFY_CONFIG.apiKey}` },
  body: formData
});
const result = await response.json();
```

**之后：**
```javascript
const result = await DifyProxyClient.uploadFile(APP_TYPE, file, USER_ID);
```

### 步骤 3: 工作流运行迁移（非流式）

**之前：**
```javascript
const payload = {
  inputs: { query: "用户输入" },
  response_mode: "blocking",
  user: DIFY_CONFIG.user
};

const response = await fetch(`${DIFY_CONFIG.baseUrl}/workflows/run`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${DIFY_CONFIG.apiKey}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
});
const result = await response.json();
```

**之后：**
```javascript
const result = await DifyProxyClient.runWorkflow(
  APP_TYPE,
  { query: "用户输入" },
  { user: USER_ID }
);
```

### 步骤 4: 工作流运行迁移（流式）

**之前：**
```javascript
const payload = {
  inputs: { query: "用户输入" },
  response_mode: "streaming",
  user: DIFY_CONFIG.user
};

const response = await fetch(`${DIFY_CONFIG.baseUrl}/workflows/run`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${DIFY_CONFIG.apiKey}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
});

const reader = response.body.getReader();
// ... 处理流式数据
```

**之后：**
```javascript
const response = await DifyProxyClient.runWorkflowStream(
  APP_TYPE,
  { query: "用户输入" },
  { user: USER_ID }
);

const reader = response.body.getReader();
// ... 处理流式数据（保持不变）
```

## API 参考

### DifyProxyClient.uploadFile()

上传文件到 Dify。

```javascript
await DifyProxyClient.uploadFile(appType, file, user)
```

**参数：**
- `appType` (string): 应用类型
  - `"order_recognition"` - 接单识别
  - `"element_extraction"` - 要素提取
  - `"dispatch_assistant"` - 派单助手
  - `"address_recognition"` - 地址识别
- `file` (File): 文件对象
- `user` (string, 可选): 用户标识

**返回：**
```javascript
{
  "id": "file-xxx",
  "name": "audio.mp3",
  // ... 其他字段
}
```

### DifyProxyClient.runWorkflow()

运行工作流（非流式）。

```javascript
await DifyProxyClient.runWorkflow(appType, inputs, options)
```

**参数：**
- `appType` (string): 应用类型
- `inputs` (object): 输入参数
- `options` (object, 可选):
  - `user` (string): 用户标识
  - `conversationId` (string): 会话ID

**返回：**
```javascript
{
  "data": {
    "outputs": { /* 工作流输出 */ }
  }
}
```

### DifyProxyClient.runWorkflowStream()

运行工作流（流式）。

```javascript
await DifyProxyClient.runWorkflowStream(appType, inputs, options)
```

**参数：** 同 `runWorkflow()`

**返回：** Response 对象（可通过 `response.body.getReader()` 读取流）

## 待迁移文件清单

- [x] `static/js/order.js` - 接单识别（已完成）
- [ ] `static/js/elements.js` - 要素提取
- [ ] `static/js/assistant.js` - 派单助手
- [ ] `static/js/tickets_local.js` - 工单列表（地址识别 + 派单）

## 安全优势

1. **API 密钥隐藏**：密钥存储在后端，前端无法访问
2. **统一管理**：所有密钥集中管理，便于更新和轮换
3. **访问控制**：可在后端添加认证、授权、速率限制
4. **审计日志**：可记录所有 API 调用，便于追踪
5. **错误处理**：统一的错误处理和日志记录

## 扩展性

添加新的 Dify 应用只需：

1. 在 `config/dify_config.py` 中添加密钥：
```python
DIFY_API_KEYS = {
    # ... 现有配置
    "new_app": "app-new-key"
}
```

2. 前端直接使用：
```javascript
const result = await DifyProxyClient.runWorkflow("new_app", inputs);
```

无需修改后端代码！

## 故障排查

### 错误：未知的应用类型

```
ValueError: 未知的应用类型: xxx
```

**解决方案**：检查 `config/dify_config.py` 中是否配置了该应用类型。

### 错误：文件上传失败

```
文件上传失败 (500): ...
```

**解决方案**：
1. 检查后端日志
2. 确认 Dify API 地址可访问
3. 验证 API 密钥是否正确

### 错误：DifyProxyClient is not defined

**解决方案**：确保在 `index.html` 中引入了 `dify_client.js`：
```html
<script src="/static/js/dify_client.js"></script>
```

## 性能考虑

- 代理层增加的延迟：< 10ms（本地网络）
- 文件上传：通过后端中转，可能略慢，但更安全
- 流式响应：无额外延迟，实时转发

## 下一步

1. 完成其他 JS 文件的迁移
2. 添加后端认证机制
3. 实施速率限制
4. 添加 API 调用监控和日志
