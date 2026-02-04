/* ================= 页面2 JS：接单识别（增强版：同步播放 + 实时显示 conversion） ================= */
// 应用类型配置（不再需要暴露 API 密钥）
const APP_TYPE = "order_recognition";
const USER_ID = "frontend-order-user";

let selectedFile = null;
let selectedObjectUrl = null; // 用于本地音频播放 URL（记得 revoke）

function logProcess(msg, type = "info") {
  const box = document.getElementById("processLog");
  if (!box) return;

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

function updateEmptyState(listId, text) {
  const list = document.getElementById(listId);
  if (!list) return;

  const hasItems = list.querySelectorAll("li").length > 0;
  let tip = list.querySelector(".empty-tip");

  if (!hasItems) {
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "empty-tip";
      tip.textContent = text;
      list.appendChild(tip);
    }
  } else {
    if (tip) tip.remove();
  }
}

function moveItem(element, targetType) {
  const text = element.textContent;
  const targetListId = targetType === "asked" ? "list-asked" : "list-missing";
  const targetList = document.getElementById(targetListId);

  const newItem = document.createElement("li");
  newItem.textContent = text;

  if (targetType === "asked") {
    newItem.className = "res-item item-asked";
    newItem.onclick = function () { moveItem(this, "missing"); };
  } else {
    newItem.className = "res-item item-missing";
    newItem.onclick = function () { moveItem(this, "asked"); };
  }

  targetList.appendChild(newItem);
  element.remove();

  updateEmptyState("list-asked", "无");
  updateEmptyState("list-missing", "信息完整");
}

function renderResult(resultData) {
  const listAsked = document.getElementById("list-asked");
  const listMissing = document.getElementById("list-missing");
  if (!listAsked || !listMissing) return;

  // resultData 允许：string / {text:"...json..."} / object
  if (typeof resultData === "string") {
    try {
      const cleanStr = resultData.replace(/```json/g, "").replace(/```/g, "").trim();
      resultData = JSON.parse(cleanStr);
    } catch (e) {
      logProcess("结果解析失败（string 非 JSON）", "error");
    }
  } else if (resultData && typeof resultData === "object" && typeof resultData.text === "string") {
    try {
      const cleanStr = resultData.text.replace(/```json/g, "").replace(/```/g, "").trim();
      resultData = JSON.parse(cleanStr);
    } catch (e) {
      // ignore
    }
  }

  const askedArr =
    (resultData && (resultData["asked_questions已经问了的问题"] || resultData["asked_questions"])) || [];
  const missingArr =
    (resultData && (resultData["missing_questions还需要追问的问题"] || resultData["missing_questions"])) || [];

  listAsked.innerHTML = "";
  listMissing.innerHTML = "";

  (askedArr || []).forEach((q) => {
    const li = document.createElement("li");
    li.className = "res-item item-asked";
    li.textContent = q;
    li.onclick = function () { moveItem(this, "missing"); };
    listAsked.appendChild(li);
  });

  (missingArr || []).forEach((q) => {
    const li = document.createElement("li");
    li.className = "res-item item-missing";
    li.textContent = q;
    li.onclick = function () { moveItem(this, "asked"); };
    listMissing.appendChild(li);
  });

  updateEmptyState("list-asked", "无");
  updateEmptyState("list-missing", "信息完整");
}

/* ========== 新增：对话内容（conversion）实时渲染 ========== */
function setConversation(text) {
  const el = document.getElementById("conversationBox");
  if (!el) return;
  el.textContent = text && String(text).trim() ? String(text) : "暂无数据";
  el.scrollTop = el.scrollHeight;
}

function clearConversation() {
  setConversation("暂无数据");
}

function tryParseJsonMaybe(s) {
  if (typeof s !== "string") return null;
  const t = s.trim();
  if (!t) return null;
  if (!((t.startsWith("{") && t.endsWith("}")) || (t.startsWith("[") && t.endsWith("]")))) return null;
  try { return JSON.parse(t); } catch { return null; }
}

function extractConversationFromOutputs(outputs) {
  if (!outputs) return null;

  // outputs 可能是 string / object
  if (typeof outputs === "string") {
    const obj = tryParseJsonMaybe(outputs);
    if (obj) return extractConversationFromOutputs(obj);
    return null;
  }

  if (typeof outputs !== "object") return null;

  // 1) 直接字段：conversion / conversation
  if (outputs.conversion) return String(outputs.conversion);
  if (outputs.conversation) return String(outputs.conversation);

  // 2) text 里可能是 JSON 字符串：{ conversion: "...", text: "..." }
  if (typeof outputs.text === "string") {
    const obj = tryParseJsonMaybe(
      outputs.text.replace(/```json/g, "").replace(/```/g, "").trim()
    );
    if (obj) {
      if (obj.conversion) return String(obj.conversion);
      if (obj.conversation) return String(obj.conversation);
    }
  }

  // 3) 某些节点可能把识别文本放在 query 字段（作为兜底）
  // （注意：这只是兜底显示，不会影响 asked/missing 的最终渲染）
  if (outputs.query && typeof outputs.query === "string") {
    const q = outputs.query.trim();
    // 简单判断：像对话那种多段换行
    if (q.includes("\n") && (q.includes("市民") || q.includes("热线") || q.includes("工作人员"))) {
      return q;
    }
  }

  return null;
}

/* ========== 新增：本地音频播放（同步播放） ========== */
function syncAudioPlayerWithFile(file) {
  const audio = document.getElementById("orderAudio");
  if (!audio) return;

  // 清理上一次 URL
  if (selectedObjectUrl) {
    try { URL.revokeObjectURL(selectedObjectUrl); } catch {}
    selectedObjectUrl = null;
  }

  if (!file) {
    audio.removeAttribute("src");
    audio.load();
    return;
  }

  selectedObjectUrl = URL.createObjectURL(file);
  audio.src = selectedObjectUrl;
  audio.load();
}

async function playSelectedAudioFromStart() {
  const audio = document.getElementById("orderAudio");
  if (!audio || !audio.src) return;

  try {
    audio.currentTime = 0;
    await audio.play(); // 在 click 触发链路中调用，避免浏览器拦截
  } catch (e) {
    console.warn("音频自动播放失败：", e);
    logProcess("提示：音频自动播放失败，可手动点击播放器播放（浏览器策略限制）", "info");
  }
}

/* ========== 主流程：上传 + dify streaming ========== */
async function startAnalysis() {
  if (!selectedFile) {
    alert("请先选择一个音频文件！");
    return;
  }

  const btn = document.getElementById("btnAnalyze");
  const listAsked = document.getElementById("list-asked");
  const listMissing = document.getElementById("list-missing");
  const logBox = document.getElementById("processLog");

  // 清空 UI
  if (listAsked) listAsked.innerHTML = "";
  if (listMissing) listMissing.innerHTML = "";
  updateEmptyState("list-asked", "等待数据...");
  updateEmptyState("list-missing", "等待数据...");

  if (logBox) logBox.innerHTML = '<div class="log-line">>>> 准备开始任务...</div>';
  clearConversation();

  btn.disabled = true;

  // ✅ 需求 1：点击开始流式分析时，同步播放录音（必须尽早执行）
  await playSelectedAudioFromStart();

  try {
    logProcess("正在上传音频文件...");

    // 使用代理客户端上传文件
    const uploadJson = await DifyProxyClient.uploadFile(APP_TYPE, selectedFile, USER_ID);
    const fileId = uploadJson.id;
    logProcess(`文件上传成功 (ID: ${fileId})`);

    logProcess("启动工作流 (流式模式)...");

    // 使用代理客户端运行流式工作流
    const response = await DifyProxyClient.runWorkflowStream(
      APP_TYPE,
      { audio: { type: "audio", transfer_method: "local_file", upload_file_id: fileId } },
      { user: USER_ID }
    );

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    // 用于避免重复刷新（但如果后续拿到更长的对话，也允许更新）
    let latestConv = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE：每个事件以 \n\n 分隔
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        if (!part.startsWith("data: ")) continue;
        const jsonStr = part.replace("data: ", "").trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);

          // ✅ 需求 2：任何事件中，只要 outputs 里出现 conversion/conversation 就立刻显示
          // Dify streaming：node_finished / workflow_finished 通常有 data.data.outputs
          const outputs = data?.data?.outputs;
          const conv = extractConversationFromOutputs(outputs);

          if (conv && conv.trim() && conv.trim() !== latestConv.trim()) {
            // 若是更长的内容（或不同），就更新显示
            if (!latestConv || conv.length >= latestConv.length) {
              latestConv = conv;
              setConversation(latestConv);
            }
          }

          // 日志与最终结果逻辑保持（按你的原逻辑）
          switch (data.event) {
            case "workflow_started":
              logProcess("工作流已启动", "info");
              break;

            case "node_started":
              logProcess(`节点开始: ${data.data?.title || "Unknown"}`, "node");
              break;

            case "node_finished":
              logProcess(`节点完成: ${data.data?.title || "Unknown"}`, "info");
              break;

            case "workflow_finished":
              if (data.data?.status === "failed") {
                logProcess(`工作流失败: ${data.data?.error || "Unknown error"}`, "error");
                break;
              }
              logProcess("工作流执行完毕，正在渲染结果...", "finish");

              // outputs 可能是：
              // { conversion: "...", text: "{ asked/missing json }" }
              // 或者 outputs 本身就是 asked/missing 的结构
              {
                const outs = data.data?.outputs || {};
                const payloadForResult = (outs && typeof outs === "object" && outs.text) ? outs.text : outs;
                renderResult(payloadForResult);

                // 如果最后才给 conversion，也兜底再刷一次
                const conv2 = extractConversationFromOutputs(outs);
                if (conv2 && conv2.trim()) {
                  latestConv = conv2;
                  setConversation(latestConv);
                }
              }
              break;

            case "error":
              logProcess(`发生错误: ${data.message || "Unknown error"}`, "error");
              break;
          }
        } catch (e) {
          console.warn("JSON解析错误", e);
        }
      }
    }
  } catch (e) {
    console.error(e);
    logProcess(`执行异常: ${e.message}`, "error");
    alert("执行失败: " + e.message);
  } finally {
    btn.disabled = false;
  }
}

// 绑定 UI
(function bindOrderEvents() {
  const uploadBox = document.getElementById("uploadBox");
  const audioInput = document.getElementById("audioInput");
  const btnAnalyze = document.getElementById("btnAnalyze");

  if (uploadBox && audioInput) {
    uploadBox.addEventListener("click", () => audioInput.click());
    audioInput.addEventListener("change", () => {
      if (audioInput.files && audioInput.files[0]) {
        selectedFile = audioInput.files[0];
        document.getElementById("fileName").textContent = "已选择: " + selectedFile.name;

        // 同步给 audio 播放器
        syncAudioPlayerWithFile(selectedFile);

        // 重置对话显示
        clearConversation();
      }
    });
  }

  if (btnAnalyze) btnAnalyze.addEventListener("click", startAnalysis);

  // 页面加载时初始化一下
  window.addEventListener("beforeunload", () => {
    if (selectedObjectUrl) {
      try { URL.revokeObjectURL(selectedObjectUrl); } catch {}
    }
  });
})();
