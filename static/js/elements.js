/* ================= 页面3 JS：诉求要素提取 ================= */
// 应用类型配置（不再需要暴露 API 密钥）
const APP_TYPE = "element_extraction";
const USER_ID = "frontend-elements-user";

function logElements(msg, type = "info") {
  const box = document.getElementById("elementsLog");
  const div = document.createElement("div");
  div.className = "log-line";
  const time = new Date().toLocaleTimeString();

  let content = `<span class="log-time">[${time}]</span> ${msg}`;
  if (type === "node") content = `<span class="log-time">[${time}]</span> <span class="log-node">⚙️ 节点执行</span> ${msg}`;
  if (type === "finish") content = `<span class="log-time">[${time}]</span> <span style="color:#0f0">✅ ${msg}</span>`;
  if (type === "error") content = `<span class="log-time">[${time}]</span> <span style="color:#f55">❌ ${msg}</span>`;

  div.innerHTML = content;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function setElementsStatus(t) {
  const el = document.getElementById("elementsStatus");
  if (el) el.textContent = t;
}

function clearElementsUI() {
  document.getElementById("elementsLog").innerHTML = '<div class="log-line">>>> 准备开始任务...</div>';
  document.getElementById("elementsKV").innerHTML = '<div class="empty-tip">暂无结果</div>';
  document.getElementById("elementsReason").innerHTML = '<div class="empty-tip">暂无结果</div>';
}

function normalizeElementsResult(outputs) {
  let data = outputs;

  if (typeof data === "string") {
    const clean = data.replace(/```json/g, "").replace(/```/g, "").trim();
    try { data = JSON.parse(clean); } catch (e) { /* ignore */ }
  } else if (data && typeof data === "object" && typeof data.text === "string") {
    const clean = data.text.replace(/```json/g, "").replace(/```/g, "").trim();
    try { data = JSON.parse(clean); } catch (e) { /* ignore */ }
  }

  if (!data || typeof data !== "object") return null;
  return data;
}

function renderElementsResult(obj) {
  const kvEl = document.getElementById("elementsKV");
  const reasonEl = document.getElementById("elementsReason");
  kvEl.innerHTML = "";
  reasonEl.innerHTML = "";

  const reason = obj.reason;
  const entries = Object.entries(obj).filter(([k]) => k !== "reason");

  if (!entries.length) {
    kvEl.innerHTML = '<div class="empty-tip">暂无结果</div>';
  } else {
    entries.forEach(([k, v]) => {
      const row = document.createElement("div");
      row.className = "kv-row";

      const key = document.createElement("div");
      key.className = "kv-key";
      key.textContent = k;

      const val = document.createElement("div");
      val.className = "kv-val";
      val.textContent = v === null || v === undefined ? "" : String(v);

      row.appendChild(key);
      row.appendChild(val);
      kvEl.appendChild(row);
    });
  }

  if (reason && String(reason).trim()) {
    const pre = document.createElement("pre");
    pre.textContent = String(reason);
    reasonEl.appendChild(pre);
  } else {
    reasonEl.innerHTML = '<div class="empty-tip">暂无结果</div>';
  }
}

async function runElementsStream() {
  const input = document.getElementById("elementsInput").value.trim();
  if (!input) {
    alert("请输入诉求内容！");
    return;
  }

  const btn = document.getElementById("btnElementsRun");
  btn.disabled = true;
  clearElementsUI();
  setElementsStatus("请求中...");

  try {
    logElements("启动工作流（流式模式）...");

    // 使用代理客户端运行流式工作流
    const response = await DifyProxyClient.runWorkflowStream(
      APP_TYPE,
      { query: input },
      { user: USER_ID }
    );

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    setElementsStatus("接收流...");
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        if (!chunk.startsWith("data: ")) continue;
        const jsonStr = chunk.replace("data: ", "").trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);
          switch (data.event) {
            case "workflow_started":
              logElements("工作流已启动");
              break;
            case "node_started":
              logElements(`节点开始: ${data.data?.title || "Unknown"}`, "node");
              break;
            case "node_finished":
              logElements(`节点完成: ${data.data?.title || "Unknown"}`);
              break;
            case "workflow_finished": {
              logElements("工作流执行完毕，正在渲染结果...", "finish");
              const outputs = data.data?.outputs;
              const obj = normalizeElementsResult(outputs);
              if (!obj) {
                logElements("结果解析失败：outputs 不是有效 JSON 对象", "error");
                setElementsStatus("完成（但解析失败）");
                break;
              }
              renderElementsResult(obj);
              setElementsStatus("完成 ✅");
              break;
            }
            case "error":
              logElements(`发生错误: ${data.message || "Unknown error"}`, "error");
              setElementsStatus("失败 ❌");
              break;
          }
        } catch (e) {
          // ignore bad lines
        }
      }
    }
  } catch (e) {
    console.error(e);
    logElements(`执行异常: ${e.message}`, "error");
    setElementsStatus("失败 ❌");
    alert("执行失败: " + e.message);
  } finally {
    btn.disabled = false;
  }
}

// 绑定按钮
(function bindElementsEvents() {
  const btn = document.getElementById("btnElementsRun");
  if (btn) btn.addEventListener("click", runElementsStream);
})();
