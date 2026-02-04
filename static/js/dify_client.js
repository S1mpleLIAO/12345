/**
 * Dify API 代理客户端
 * 通过后端代理调用 Dify API，隐藏 API 密钥
 */

const DifyProxyClient = {
  /**
   * 上传文件到 Dify
   * @param {string} appType - 应用类型 (order_recognition, element_extraction, dispatch_assistant, address_recognition)
   * @param {File} file - 文件对象
   * @param {string} user - 用户标识（可选）
   * @returns {Promise<Object>} - 上传响应，包含 file_id
   */
  async uploadFile(appType, file, user = null) {
    const formData = new FormData();
    formData.append("app_type", appType);
    formData.append("file", file);
    if (user) {
      formData.append("user", user);
    }

    const response = await fetch("/api/dify/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`文件上传失败 (${response.status}): ${error}`);
    }

    return await response.json();
  },

  /**
   * 运行工作流（非流式）
   * @param {string} appType - 应用类型
   * @param {Object} inputs - 输入参数
   * @param {Object} options - 可选参数
   * @param {string} options.user - 用户标识
   * @param {string} options.conversationId - 会话ID
   * @returns {Promise<Object>} - 工作流响应
   */
  async runWorkflow(appType, inputs, options = {}) {
    const payload = {
      app_type: appType,
      inputs: inputs,
      response_mode: "blocking",
      user: options.user || null,
      conversation_id: options.conversationId || null,
    };

    const response = await fetch("/api/dify/workflow", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`工作流执行失败 (${response.status}): ${error}`);
    }

    return await response.json();
  },

  /**
   * 运行工作流（流式）
   * @param {string} appType - 应用类型
   * @param {Object} inputs - 输入参数
   * @param {Object} options - 可选参数
   * @param {string} options.user - 用户标识
   * @param {string} options.conversationId - 会话ID
   * @returns {Promise<Response>} - 流式响应对象
   */
  async runWorkflowStream(appType, inputs, options = {}) {
    const payload = {
      app_type: appType,
      inputs: inputs,
      response_mode: "streaming",
      user: options.user || null,
      conversation_id: options.conversationId || null,
    };

    const response = await fetch("/api/dify/workflow/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`流式工作流执行失败 (${response.status}): ${error}`);
    }

    return response;
  },
};

// 导出供其他模块使用
if (typeof module !== "undefined" && module.exports) {
  module.exports = DifyProxyClient;
}
