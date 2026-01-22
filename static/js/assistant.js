/* ================= 页面：接单助手（文本 -> Dify workflow） ================= */

const DIFY_ASSIST_CONFIG = {
  apiKey: "app-ja847DdFKufaS29cIeAn3WKl",
  workflowRunUrl: "http://121.43.245.245:5001/v1/workflows/run",
  user: "abc-123",
  conversation_id: ""
};

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

/**
 * outputs 可能是：
 * 1) { department, reason, history, rules }
 * 2) { text: "..." } / { result: "..." } 等
 * 3) text 里本身是 JSON 字符串
 */
function pickDeptReason(outputs) {
  if (!outputs) return "—";

  // 优先结构化字段
  const deptRaw = outputs.department || outputs.dept || "";
  const reasonRaw = outputs.reason || "";

  if (deptRaw || reasonRaw) {
    const dept = String(deptRaw).replace(/^处置部门[:：]?\s*/, "").trim();

    let reason = String(reasonRaw || "").trim();

    return `处置部门：${dept || "—"}\n理由：${reason || "—"}`;
  }

  // 否则尝试从文本里抽取
  const text = (outputs.text ?? outputs.result ?? outputs.answer ?? outputs.output ?? "")
    .toString()
    .trim();

  if (!text) return "—";

  // 尝试按行提取 “处置部门/理由”
  let dept = "";
  let reason = "";
  const lines = text.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);

  for (const ln of lines) {
    if (!dept && (ln.startsWith("处置部门") || ln.startsWith("承办部门") || ln.startsWith("部门"))) {
      dept = ln.replace(/^.*?[:：]\s*/, "").trim();
      continue;
    }
    if (!reason && ln.startsWith("理由")) {
      reason = ln.replace(/^.*?[:：]\s*/, "").trim();
      continue;
    }
  }

  if (!dept) {
    const m = text.match(/处置部门\s*[:：]\s*([^\n\r]+)/);
    if (m) dept = (m[1] || "").trim();
  }

  if (!reason) {
    const m = text.match(/理由\s*[:：]\s*([\s\S]+)/);
    if (m) reason = (m[1] || "").trim();
  }


  if (dept || reason) return `处置部门：${dept || "—"}\n理由：${reason || "—"}`;


}

async function runDifyAssist(query) {
  const payload = {
    inputs: { query },
    conversation_id: DIFY_ASSIST_CONFIG.conversation_id,
    user: DIFY_ASSIST_CONFIG.user
  };

  const resp = await fetch(DIFY_ASSIST_CONFIG.workflowRunUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${DIFY_ASSIST_CONFIG.apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!resp.ok) {
    const t = await resp.text().catch(() => "");
    throw new Error(`工作流调用失败 (${resp.status}) ${t}`);
  }

  const data = await resp.json();

  // dify 标准：data.data.outputs
  let outputs = data?.data?.outputs ?? data?.outputs ?? {};

  // 情况 A：outputs 已经是结构化（你后端监控看到的那种）
  if (outputs && (outputs.department || outputs.reason || outputs.history || outputs.rules)) {
    return { raw: data, outputs };
  }

  // 情况 B：outputs 里只有 text/result/answer 且可能是 JSON 字符串
  const maybeText =
    outputs?.text ?? outputs?.result ?? outputs?.answer ?? outputs?.output ?? "";

  if (typeof maybeText === "string") {
    const s = maybeText.trim();
    // 若是 JSON 字符串，parse 成对象
    if ((s.startsWith("{") && s.endsWith("}")) || (s.startsWith("[") && s.endsWith("]"))) {
      try {
        outputs = JSON.parse(s);
        return { raw: data, outputs };
      } catch (e) {
        // parse 失败就当普通文本
      }
    }
  }

  // 情况 C：普通文本
  return { raw: data, outputs: { text: maybeText } };
}

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
    const concise = pickDeptReason(outputs);
    if (placeholder) placeholder.textContent = concise;
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
})();
