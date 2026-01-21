// 页面切换（用 data-page 绑定，避免在 HTML 里写 onclick）
(function initNav() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((el) => {
    el.addEventListener("click", () => {
      const pageId = el.getAttribute("data-page");
      switchPage(pageId, el);
    });
  });
})();

function switchPage(pageId, navEl) {
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.remove("active"));
  navEl.classList.add("active");

  document.querySelectorAll(".page-view").forEach((el) => (el.style.display = "none"));
  document.getElementById("page-" + pageId).style.display = "flex";
}

// 默认初始化日期/年份（原逻辑保持）
(function initDefault() {
  const d = new Date();
  const dateEl = document.getElementById("date");
  const yearEl = document.getElementById("year");
  if (dateEl) dateEl.value = new Date().toISOString().split("T")[0];
  if (yearEl) yearEl.value = d.getFullYear();
})();
// 默认进入工单列表（tickets）
window.addEventListener("DOMContentLoaded", () => {
  const nav = document.querySelector('.nav-item[data-page="order"]');
  if (nav) nav.click();
});
