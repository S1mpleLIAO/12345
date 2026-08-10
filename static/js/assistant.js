/* ================= 页面：接单助手（文本 -> Dify workflow，带"详情"弹窗） ================= */

// 应用类型配置（不再需要暴露 API 密钥）
const APP_TYPE_ASSISTANT = "dispatch_assistant";
const USER_ID = "frontend-assistant-user";
let conversationId = "";  // 会话ID，用于保持上下文

function $(id) {
  return document.getElementById(id);
}

function appendMsg(role, text) {
  const box = $("assistantMsgs");
  if (!box) return null;

  // 清空空态提示
  const empty = box.querySelector(".assistant-empty");
  if (empty) empty.remove();

  const row = document.createElement("div");
  row.className = "msg " + (role === "user" ? "user" : "bot");

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  box.appendChild(row);
  box.scrollTop = box.scrollHeight;

  return bubble; // 返回气泡，便于后续更新内容
}

/* ============ 解析 outputs：你给的 dify 返回是 JSON 字符串 ============ */

function safeJsonParse(str) {
  if (typeof str !== "string") return null;
  const s = str.trim();
  if (!s) return null;
  if (!((s.startsWith("{") && s.endsWith("}")) || (s.startsWith("[") && s.endsWith("]")))) return null;
  try { return JSON.parse(s); } catch { return null; }
}

async function runDifyAssist(query) {
  // 使用代理客户端运行工作流
  const data = await DifyProxyClient.runWorkflow(
    APP_TYPE_ASSISTANT,
    { query },
    { user: USER_ID, conversationId: conversationId || null }
  );

  let outputs = data?.data?.outputs ?? data?.outputs ?? {};

  // 1) outputs 已结构化
  if (outputs && (outputs.department || outputs.reason || outputs.history || outputs.rules)) {
    return { raw: data, outputs };
  }

  // 2) outputs.text/result/answer 是 JSON 字符串
  const maybeText =
    outputs?.text ?? outputs?.result ?? outputs?.answer ?? outputs?.output ?? "";

  if (typeof maybeText === "string") {
    const parsed = safeJsonParse(maybeText);
    if (parsed) return { raw: data, outputs: parsed };
  }

  // 3) 普通文本
  return { raw: data, outputs: { text: String(maybeText || "").trim() } };
}

/* ============ 详情弹窗：渲染 history/rules（三条） ============ */

function showMask(show) {
  const mask = $("assistDetailMask");
  if (!mask) return;
  mask.style.display = show ? "flex" : "none";
}

function extractTextAndLabel(contentStr) {
  // content 类似： text\":\"......\";\"label\":\"属地\"
  if (typeof contentStr !== "string") return { text: String(contentStr || ""), label: "" };
  const s = contentStr.replace(/\\"/g, '"'); // 反转义
  const mText = s.match(/text"\s*:\s*"([\s\S]*?)"\s*;?/);
  const mLabel = s.match(/label"\s*:\s*"([\s\S]*?)"\s*;?/);
  return {
    text: (mText?.[1] || s).trim(),
    label: (mLabel?.[1] || "").trim()
  };
}

function renderDetailList(containerId, items) {
  const box = $(containerId);
  if (!box) return;
  box.innerHTML = "";

  const arr = Array.isArray(items) ? items.slice(0, 3) : [];

  if (arr.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-tip";
    empty.textContent = "暂无数据";
    box.appendChild(empty);
    return;
  }

  arr.forEach((it, idx) => {
    const { text, label } = extractTextAndLabel(it?.content || "");
    const sourceType = it?.source_type || "";

    const card = document.createElement("div");
    card.className = "assist-item";

    const top = document.createElement("div");
    top.className = "assist-item-top";

    const badge = document.createElement("div");
    badge.className = "assist-item-badge";
    badge.textContent = label ? label : `条目 ${idx + 1}`;

    const type = document.createElement("div");
    type.className = "assist-item-type";
    type.textContent = sourceType ? sourceType : "";

    top.appendChild(badge);
    top.appendChild(type);

    const body = document.createElement("div");
    body.className = "assist-item-text";
    body.textContent = text;

    card.appendChild(top);
    card.appendChild(body);
    box.appendChild(card);
  });
}

function openDetail(outputs) {
  renderDetailList("assistHistoryList", outputs?.history || []);
  renderDetailList("assistRulesList", outputs?.rules || []);
  showMask(true);
}

/* ============ 回答渲染：reason 旁边加“详情”按钮 ============ */

function renderAssistAnswer(bubble, outputs) {
  if (!bubble) return;

  // 若不是结构化，按普通文本显示
  if (!outputs || (typeof outputs === "object" && outputs.text && !outputs.department && !outputs.reason)) {
    bubble.textContent = outputs?.text || "—";
    return;
  }

  const deptRaw = outputs.department || outputs.dept || "";
  const reasonRaw = outputs.reason || "";

  const dept = String(deptRaw || "").trim();
  const reason = String(reasonRaw || "").trim();

  bubble.innerHTML = "";

  const wrap = document.createElement("div");
  wrap.className = "assist-answer";

  const head = document.createElement("div");
  head.className = "assist-answer-head";

  const deptEl = document.createElement("div");
  deptEl.className = "assist-dept";
  deptEl.textContent = dept || "处置部门：—";

  head.appendChild(deptEl);

  const hasDetail =
    (Array.isArray(outputs.history) && outputs.history.length > 0) ||
    (Array.isArray(outputs.rules) && outputs.rules.length > 0);

  if (hasDetail) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "assist-detail-btn";
    btn.textContent = "详情";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openDetail(outputs);
    });
    head.appendChild(btn);
  }

  const pre = document.createElement("pre");
  pre.className = "assist-reason";
  pre.textContent = reason ? reason : "—";

  wrap.appendChild(head);
  wrap.appendChild(pre);
  bubble.appendChild(wrap);
}

/* ============ 发送逻辑 ============ */

async function sendAssist() {
  const inputEl = $("assistantInput");
  const btn = $("assistantSend");
  if (!inputEl || !btn) return;

  const query = inputEl.value.trim();
  if (!query) {
    alert("请输入诉求内容！");
    return;
  }

  appendMsg("user", query);
  inputEl.value = "";

  btn.disabled = true;
  const placeholder = appendMsg("bot", "处理中…");

  try {
    const { outputs } = await runDifyAssist(query);

    // 你的 dify 返回是一个 JSON 字符串，runDifyAssist 已经 parse 了
    // 这里直接渲染 department/reason + 详情(history/rules)
    renderAssistAnswer(placeholder, outputs);
  } catch (e) {
    console.error(e);
    if (placeholder) placeholder.textContent = "失败：" + (e.message || String(e));
  } finally {
    btn.disabled = false;
  }
}

(function bindAssistant() {
  const btn = $("assistantSend");
  const input = $("assistantInput");

  if (btn) btn.addEventListener("click", sendAssist);

  if (input) {
    input.addEventListener("keydown", (e) => {
      // Enter 发送，Ctrl+Enter 换行
      if (e.key === "Enter" && !e.ctrlKey) {
        e.preventDefault();
        sendAssist();
      }
    });
  }

  // 弹窗关闭
  const closeBtn = $("assistDetailClose");
  const mask = $("assistDetailMask");

  if (closeBtn) closeBtn.addEventListener("click", () => showMask(false));
  if (mask) {
    mask.addEventListener("click", (e) => {
      // 点遮罩关闭，点内容不关闭
      if (e.target === mask) showMask(false);
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") showMask(false);
  });
})();
