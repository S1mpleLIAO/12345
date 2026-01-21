/* ================= 页面2 JS：接单识别 ================= */
const DIFY_CONFIG = {
  apiKey: "app-rBYgj9vKWewVLflK64xFtDap",
  baseUrl: "http://121.43.245.245:5001/v1",
  user: "frontend-direct-user",
};

let selectedFile = null;

function logProcess(msg, type = "info") {
  const box = document.getElementById("processLog");
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

  if (typeof resultData === "string") {
    try {
      const cleanStr = resultData.replace(/```json/g, "").replace(/```/g, "").trim();
      resultData = JSON.parse(cleanStr);
    } catch (e) {
      logProcess("结果解析失败", "error");
    }
  } else if (resultData && resultData.text) {
    try {
      const cleanStr = resultData.text.replace(/```json/g, "").replace(/```/g, "").trim();
      resultData = JSON.parse(cleanStr);
    } catch (e) {
      // ignore
    }
  }

  const askedArr = resultData["asked_questions已经问了的问题"] || resultData["asked_questions"] || [];
  const missingArr = resultData["missing_questions还需要追问的问题"] || resultData["missing_questions"] || [];

  listAsked.innerHTML = "";
  listMissing.innerHTML = "";

  askedArr.forEach((q) => {
    const li = document.createElement("li");
    li.className = "res-item item-asked";
    li.textContent = q;
    li.onclick = function () { moveItem(this, "missing"); };
    listAsked.appendChild(li);
  });

  missingArr.forEach((q) => {
    const li = document.createElement("li");
    li.className = "res-item item-missing";
    li.textContent = q;
    li.onclick = function () { moveItem(this, "asked"); };
    listMissing.appendChild(li);
  });

  updateEmptyState("list-asked", "无");
  updateEmptyState("list-missing", "信息完整");
}

async function startAnalysis() {
  if (!selectedFile) {
    alert("请先选择一个音频文件！");
    return;
  }

  const btn = document.getElementById("btnAnalyze");
  const listAsked = document.getElementById("list-asked");
  const listMissing = document.getElementById("list-missing");
  const logBox = document.getElementById("processLog");

  listAsked.innerHTML = "";
  listMissing.innerHTML = "";
  updateEmptyState("list-asked", "等待数据...");
  updateEmptyState("list-missing", "等待数据...");

  logBox.innerHTML = '<div class="log-line">>>> 准备开始任务...</div>';
  btn.disabled = true;

  try {
    logProcess("正在上传音频文件...");
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("user", DIFY_CONFIG.user);

    const uploadResp = await fetch(`${DIFY_CONFIG.baseUrl}/files/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${DIFY_CONFIG.apiKey}` },
      body: formData,
    });
    if (!uploadResp.ok) throw new Error(`上传失败 (${uploadResp.status})`);

    const uploadJson = await uploadResp.json();
    const fileId = uploadJson.id;
    logProcess(`文件上传成功 (ID: ${fileId})`);

    logProcess("启动工作流 (流式模式)...");
    const payload = {
      inputs: { audio: { type: "audio", transfer_method: "local_file", upload_file_id: fileId } },
      response_mode: "streaming",
      user: DIFY_CONFIG.user,
    };

    const response = await fetch(`${DIFY_CONFIG.baseUrl}/workflows/run`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${DIFY_CONFIG.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) throw new Error(`工作流调用失败 (${response.status})`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.replace("data: ", "").trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);
          switch (data.event) {
            case "workflow_started":
              logProcess("工作流已启动", "info");
              break;
            case "node_started":
              logProcess(`节点开始: ${data.data.title || "Unknown"}`, "node");
              break;
            case "node_finished":
              logProcess(`节点完成: ${data.data.title || "Unknown"}`, "info");
              break;
            case "workflow_finished":
              logProcess("工作流执行完毕，正在渲染结果...", "finish");
              renderResult(data.data.outputs);
              break;
            case "error":
              logProcess(`发生错误: ${data.message}`, "error");
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
      }
    });
  }

  if (btnAnalyze) btnAnalyze.addEventListener("click", startAnalysis);
})();
