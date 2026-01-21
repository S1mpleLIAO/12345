/* ================= 页面1 JS：报表生成 ================= */
let PLANS = {};
let ACTIVE_SECTION = null;

function setStatus(t) {
  document.getElementById("status").textContent = t;
}
function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}
function clip(s, n = 900) {
  if (!s) return "";
  return s.length <= n ? s : s.slice(0, n) + " ...<truncated>";
}

function clearPanels() {
  PLANS = {};
  ACTIVE_SECTION = null;
  document.getElementById("plan-area").style.display = "none";
  document.getElementById("plan-meta").textContent = "";
  document.getElementById("plan-note").textContent = "";
  document.getElementById("seg-tabs").innerHTML = "";
  document.getElementById("steps").innerHTML = "";
  document.getElementById("progress-bar").style.width = "0%";
  document.getElementById("trace-detail").innerHTML = "";
  document.getElementById("trace-fallback").innerHTML = "";
  document.getElementById("result").innerHTML = '<div class="placeholder">生成中…</div>';
}

function addEventCard(containerId, title, badgeText, metaText, contentText, extraObj) {
  const trace = document.getElementById(containerId);
  if (!trace) return;

  const div = document.createElement("div");
  div.className = "evt";
  div.innerHTML = `<div class="top"><div class="title"><span class="badge">${escapeHtml(badgeText)}</span> ${escapeHtml(
    title
  )}</div><div class="meta">${escapeHtml(metaText)}</div></div>`;

  if (contentText && contentText.trim()) {
    const pre = document.createElement("pre");
    pre.textContent = contentText;
    div.appendChild(pre);
  }
  if (extraObj) {
    const det = document.createElement("details");
    const sum = document.createElement("summary");
    sum.textContent = "查看原始事件 JSON";
    det.appendChild(sum);
    const pre2 = document.createElement("pre");
    pre2.textContent = JSON.stringify(extraObj, null, 2);
    det.appendChild(pre2);
    div.appendChild(det);
  }
  trace.appendChild(div);
  trace.scrollTop = trace.scrollHeight;
}

function showPlanArea() {
  document.getElementById("plan-area").style.display = "block";
  document.getElementById("trace-fallback").style.display = "none";
}

function sectionLabel(sec) {
  const m = {
    daily: "主体日报",
    bottom3_trend: "倒三趋势",
    street_table: "街道表",
    unit_table: "区直表",
    heating_season: "供暖季",
    heating_offseason: "非供暖季",
    emergency: "紧急分析",
    main: "主流程",
  };
  return m[sec] || sec;
}

function rebuildTabs() {
  const tabsEl = document.getElementById("seg-tabs");
  const secs = Object.keys(PLANS);
  if (!secs.length) {
    tabsEl.innerHTML = "";
    return;
  }
  if (!ACTIVE_SECTION || !PLANS[ACTIVE_SECTION]) ACTIVE_SECTION = secs[0];

  tabsEl.innerHTML = secs
    .map((sec) => {
      const p = PLANS[sec];
      const done = p.done_steps ? p.done_steps.size : 0;
      const total = (p.steps || []).length || 1;
      const activeCls = sec === ACTIVE_SECTION ? "active" : "";
      return `<button class="seg-tab ${activeCls}" data-sec="${sec}">${escapeHtml(sectionLabel(sec))} · ${done}/${total}</button>`;
    })
    .join("");

  // 绑定 tab 点击
  tabsEl.querySelectorAll(".seg-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sec = btn.getAttribute("data-sec");
      ACTIVE_SECTION = sec;
      renderActivePlan("切换到：" + sectionLabel(sec));
      rebuildTabs();
    });
  });
}

function renderActivePlan(noteOverride) {
  if (!ACTIVE_SECTION || !PLANS[ACTIVE_SECTION]) return;
  showPlanArea();
  const p = PLANS[ACTIVE_SECTION];
  const steps = p.steps || [];
  const total = steps.length || 1;
  const activeStep = p.active_step || 1;

  document.getElementById("plan-meta").textContent = `当前：${sectionLabel(ACTIVE_SECTION)} · 第 ${Math.min(
    activeStep,
    total
  )} / ${total} 步`;
  document.getElementById("plan-note").textContent = noteOverride || p.note || "";

  const pct = Math.max(0, Math.min(100, Math.round(((p.done_steps ? p.done_steps.size : 0) / total) * 100)));
  document.getElementById("progress-bar").style.width = pct + "%";

  document.getElementById("steps").innerHTML = steps
    .map((s) => {
      const isDone = p.done_steps && p.done_steps.has(s.step);
      const isActive = !isDone && s.step === activeStep;
      const cls = isDone ? "step-item done" : isActive ? "step-item active" : "step-item";
      const icon = isDone ? "✅" : isActive ? "▶️" : "•";
      return `<div class="${cls}">
        <div class="step-top">
          <div class="step-title">${icon} Step ${s.step}：${escapeHtml(s.title || "")}</div>
          <div class="step-tool">${escapeHtml(s.tool || "")}</div>
        </div>
        <div class="step-sub">${escapeHtml(s.hint || "")}</div>
      </div>`;
    })
    .join("");
}

function renderMarkdown(report) {
  const resultEl = document.getElementById("result");
  if (window.marked && typeof window.marked.parse === "function") {
    resultEl.innerHTML = `<div class="markdown-body">${window.marked.parse(report || "")}</div>`;
  } else {
    resultEl.innerHTML = `<pre style="white-space:pre-wrap;">${escapeHtml(report || "")}</pre>`;
  }
}

function detailedContainer() {
  return Object.keys(PLANS).length ? "trace-detail" : "trace-fallback";
}
function ensurePlan(sec) {
  if (!PLANS[sec]) PLANS[sec] = { steps: [], active_step: 1, done_steps: new Set(), note: "" };
}

function renderTraceEvent(evt) {
  const sec = evt.section || "main";
  const cont = detailedContainer();
  const round = evt.round != null ? `Round ${evt.round}` : "";

  if (evt.type === "plan") {
    ensurePlan(sec);
    PLANS[sec].steps = (evt.steps || []).map((s) => ({ ...s, hint: s.hint || "执行" }));
    PLANS[sec].active_step = evt.current_step || 1;
    PLANS[sec].note = evt.note;
    ACTIVE_SECTION = sec;
    showPlanArea();
    rebuildTabs();
    renderActivePlan(evt.note);
    addEventCard(cont, "生成计划", `${sec}`, round, evt.note);
    return;
  }

  if (evt.type === "tool_start") {
    ensurePlan(sec);
    ACTIVE_SECTION = sec;
    if (evt.step) {
      PLANS[sec].active_step = evt.step;
      renderActivePlan(`正在执行 Step ${evt.step}...`);
    }
    addEventCard(cont, `调用工具: ${evt.name}`, `${sec}`, round, JSON.stringify(evt.args));
    return;
  }

  if (evt.type === "tool_end") {
    ensurePlan(sec);
    ACTIVE_SECTION = sec;
    if (evt.step) {
      PLANS[sec].done_steps.add(evt.step);
      renderActivePlan(`Step ${evt.step} 完成`);
    }
    addEventCard(cont, `工具返回: ${evt.name}`, `${sec}`, round, clip(evt.output || ""));
    return;
  }

  if (evt.type === "final" || evt.type === "error") return;
  addEventCard(cont, `事件: ${evt.type}`, `${sec}`, round, "");
}

function onTypeChange() {
  const t = document.getElementById("reportType").value;
  document.getElementById("dateWrap").style.display = t === "heating" ? "none" : "inline-flex";
  document.getElementById("yearWrap").style.display = t === "heating" ? "inline-flex" : "none";
}

async function runStream() {
  const btn = document.getElementById("btn");
  const reportType = document.getElementById("reportType").value;
  const payload = { report_type: reportType };

  if (reportType === "heating") {
    payload.year = parseInt(document.getElementById("year").value || 0);
    if (!payload.year) {
      alert("请输入年份");
      return;
    }
  } else {
    payload.date = document.getElementById("date").value;
    if (!payload.date) {
      alert("请选择日期");
      return;
    }
  }

  btn.disabled = true;
  clearPanels();
  setStatus("请求中...");

  try {
    const resp = await fetch("/api/generate/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(resp.statusText);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    setStatus("接收流...");

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const line = part.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;

        try {
          const msg = JSON.parse(line.slice(6));
          if (msg.type === "event") renderTraceEvent(msg.data);
          else if (msg.type === "final") {
            renderMarkdown(msg.data.report);
            setStatus("完成 ✅");
            for (let k in PLANS) {
              let p = PLANS[k];
              (p.steps || []).forEach((s) => p.done_steps.add(s.step));
            }
            renderActivePlan("最终报告已生成");
          } else if (msg.type === "error") throw new Error(msg.data.message);
        } catch (e) {
          // ignore
        }
      }
    }
    setStatus("结束");
  } catch (e) {
    console.error(e);
    setStatus("失败 ❌");
    document.getElementById("result").innerText = e.message;
  } finally {
    btn.disabled = false;
  }
}

// 绑定事件（原来的 onchange/onclick 拆出来）
(function bindReportEvents() {
  const typeEl = document.getElementById("reportType");
  const btn = document.getElementById("btn");
  if (typeEl) typeEl.addEventListener("change", onTypeChange);
  if (btn) btn.addEventListener("click", runStream);

  // init: 同原逻辑
  onTypeChange();
})();
