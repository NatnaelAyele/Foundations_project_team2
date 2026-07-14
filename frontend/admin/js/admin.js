/* =====================================================================
   FreshLink — Admin Console (shared JS across all admin pages)
   Maps to: farmers, harvest_forecasts, sectors, trip_allocations,
   coordination_plans. Replace API stubs with FastAPI when ready.
   ===================================================================== */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function initTheme() {
  const btn = $("#themeToggle");
  if (!btn) return;
  const apply = (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("freshlink-theme", theme); } catch (e) {}
  };
  btn.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    apply(cur === "light" ? "dark" : "light");
  });
}

/* ---------- sidebar ---------- */
function initSidebar() {
  const sidebar = $("#sidebar");
  const collapse = $("#sidebarCollapse");
  const menuToggle = $("#menuToggle");

  // desktop collapse
  if (collapse) {
    collapse.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
  }

  // restore saved width
  try {
    const savedW = localStorage.getItem("freshlink-sidebar-w");
    if (savedW) document.documentElement.style.setProperty("--sb-w", savedW + "px");
  } catch (e) {}

  // drag-to-resize
  const handle = $("#resizeHandle");
  if (handle) {
    let dragging = false;
    const MIN = 200, MAX = 420;
    const onMove = (e) => {
      if (!dragging) return;
      const w = Math.max(MIN, Math.min(MAX, e.clientX));
      document.documentElement.style.setProperty("--sb-w", w + "px");
    };
    const stop = () => {
      if (!dragging) return;
      dragging = false;
      handle.classList.remove("dragging");
      document.body.classList.remove("resizing");
      const w = getComputedStyle(document.documentElement).getPropertyValue("--sb-w").trim().replace("px", "");
      try { localStorage.setItem("freshlink-sidebar-w", w); } catch (e) {}
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", stop);
    };
    handle.addEventListener("mousedown", (e) => {
      if (sidebar.classList.contains("collapsed")) return;
      dragging = true;
      handle.classList.add("dragging");
      document.body.classList.add("resizing");
      e.preventDefault();
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", stop);
    });
    handle.addEventListener("dblclick", () => {
      document.documentElement.style.setProperty("--sb-w", "256px");
      try { localStorage.setItem("freshlink-sidebar-w", "256"); } catch (e) {}
    });
  }
}

function initGreetingAndDate() {
  const now = new Date();
  const h = now.getHours();
  const greet = h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
  const g = $("#greeting"); if (g) g.textContent = greet + ", Admin";
  const d = $("#todayDate");
  if (d) d.textContent = now.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}

function animateCount(el) {
  const raw = el.dataset.target || "0";
  const suffix = el.dataset.suffix || "";
  const target = Number(raw);
  if (!target) { el.textContent = raw + suffix; return; }
  const dur = 900, start = performance.now();
  function tick(now) {
    const p = Math.min((now - start) / dur, 1);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))).toLocaleString("en-US") + suffix;
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
function initCounts() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    $$(".count").forEach((el) => (el.textContent = (el.dataset.target || "0") + (el.dataset.suffix || "")));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { animateCount(e.target); io.unobserve(e.target); } });
  }, { threshold: 0.4 });
  $$(".count").forEach((el) => io.observe(el));
}

function initTableSearch(inputId, tbodyId, noResultsId) {
  const input = $("#" + inputId);
  const tbody = $("#" + tbodyId);
  if (!input || !tbody) return;
  const noResults = noResultsId ? $("#" + noResultsId) : null;
  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    let shown = 0;
    $$("tr", tbody).forEach((row) => {
      const match = row.textContent.toLowerCase().includes(q);
      row.style.display = match ? "" : "none";
      if (match) shown++;
    });
    if (noResults) noResults.style.display = shown === 0 ? "block" : "none";
  });
}

function initForm(formId, successId) {
  const form = $("#" + formId);
  if (!form) return;
  const success = successId ? $("#" + successId) : null;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    let valid = true;
    $$("input[required], select[required], textarea[required]", form).forEach((field) => {
      const wrap = field.closest(".field");
      const ok = field.value && field.value.trim() !== "";
      if (wrap) wrap.classList.toggle("error", !ok);
      if (!ok) valid = false;
    });
    const radioGroups = new Set();
    $$('input[type="radio"][required]', form).forEach((r) => radioGroups.add(r.name));
    radioGroups.forEach((name) => {
      const checked = form.querySelector(`input[name="${name}"]:checked`);
      const wrap = form.querySelector(`input[name="${name}"]`).closest(".field");
      if (wrap) wrap.classList.toggle("error", !checked);
      if (!checked) valid = false;
    });
    if (!valid) return;
    // API POST goes here, e.g. fetch("/api/farmers", {method:"POST", body:new FormData(form)})
    if (success) {
      success.classList.add("show");
      form.reset();
      success.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => success.classList.remove("show"), 4000);
    }
  });
  $$("input, select, textarea", form).forEach((field) => {
    field.addEventListener("input", () => field.closest(".field")?.classList.remove("error"));
    field.addEventListener("change", () => field.closest(".field")?.classList.remove("error"));
  });
}

function initReportBars() {
  const bars = $$(".bar-fill");
  if (!bars.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        const w = e.target.dataset.width || "0%";
        requestAnimationFrame(() => { e.target.style.width = w; });
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });
  bars.forEach((b) => io.observe(b));
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSidebar();
  initGreetingAndDate();
  initCounts();
  initReportBars();
  initTableSearch("farmer-search", "farmer-table-body", "farmer-no-results");
  initTableSearch("forecast-search", "forecast-table-body", "forecast-no-results");
  initForm("register-farmer-form", "register-success");
  initForm("forecast-form", "forecast-success");
});