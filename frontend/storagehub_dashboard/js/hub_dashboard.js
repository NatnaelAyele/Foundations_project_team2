/* =====================================================================
   FreshLink — Hub Dashboard
   All data maps to real tables: cold_hubs, trip_allocations,
   forecast_allocations, farmers. The API layer below is where your
   FastAPI endpoints plug in — the UI already speaks the right shape.
   ===================================================================== */

/* ---------- tiny helpers ---------- */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* ---------- API layer (stub → replace fetch URLs when backend is ready) ---------- */
const HubAPI = {
  // GET /api/hubs/{hub_id}  → { available_capacity_kg, total_capacity_kg, ... }
  async getHub() {
    // return (await fetch(`/api/hubs/${HUB_ID}`)).json();
    return { available_capacity_kg: 850, total_capacity_kg: 2000, name: "Kamonyi Central Storage Hub" };
  },
  // GET /api/hubs/{hub_id}/allocations → [{ allocation_id, farmer, quantity_kg, expected_pickup, status }]
  async getAllocations() {
    // return (await fetch(`/api/hubs/${HUB_ID}/allocations`)).json();
    return null; // using server-rendered rows for the prototype
  },
  // POST /api/allocations/{allocation_id}/confirm  → marks trip_allocation confirmed
  async confirmReceived(allocationId) {
    // return (await fetch(`/api/allocations/${allocationId}/confirm`, { method: "POST" })).json();
    return { ok: true, allocation_id: allocationId };
  },
};

/* ---------- greeting + date ---------- */
function initGreetingAndDate() {
  const now = new Date();
  const h = now.getHours();
  const greet = h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
  const g = $("#greeting");
  if (g) g.textContent = greet;

  const d = $("#todayDate");
  if (d) {
    d.textContent = now.toLocaleDateString("en-GB", {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    });
  }
}

/* ---------- count-up animation on stat numbers ---------- */
function animateCount(el) {
  const target = Number(el.dataset.target || "0");
  if (!target) { el.textContent = "0"; return; }
  const dur = 900;
  const start = performance.now();
  const fmt = (n) => n.toLocaleString("en-US");
  function tick(now) {
    const p = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(Math.round(target * eased));
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
function initCounts() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    $$(".count").forEach((el) => (el.textContent = Number(el.dataset.target || 0).toLocaleString("en-US")));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { animateCount(e.target); io.unobserve(e.target); }
    });
  }, { threshold: 0.4 });
  $$(".count").forEach((el) => io.observe(el));
}

/* ---------- capacity gauge ---------- */
function drawGauge() {
  const gauge = $("#capacityGauge");
  if (!gauge) return;
  const avail = Number(gauge.dataset.available || 0);
  const total = Number(gauge.dataset.total || 1);
  const pctFree = total > 0 ? Math.round((avail / total) * 100) : 0;

  const fill = $(".gauge-fill", gauge);
  const circumference = 2 * Math.PI * 52; // r=52 → ~327
  const offset = circumference - (pctFree / 100) * circumference;

  // colour shifts with how full it is
  let colour = "#1f7a4d";           // plenty free
  if (pctFree <= 20) colour = "#d64545";   // nearly full
  else if (pctFree <= 45) colour = "#d97706";
  fill.style.stroke = colour;

  // animate
  requestAnimationFrame(() => { fill.style.strokeDashoffset = String(offset); });

  const pctEl = $("#gaugePct");
  if (pctEl) {
    // count the percent up too
    let cur = 0;
    const step = () => {
      cur += Math.max(1, Math.round(pctFree / 24));
      if (cur >= pctFree) cur = pctFree;
      pctEl.textContent = cur + "%";
      if (cur < pctFree) requestAnimationFrame(step);
    };
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) pctEl.textContent = pctFree + "%";
    else requestAnimationFrame(step);
  }
  const availNote = $("#availPct");
  if (availNote) availNote.textContent = pctFree + "% free";
}

/* ---------- confirm received ---------- */
function initConfirmButtons() {
  $$(".btn-confirm").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.rowId;
      btn.disabled = true;
      btn.textContent = "Confirming…";
      try {
        const res = await HubAPI.confirmReceived(id);
        if (res.ok) {
          const row = $(`tr[data-row-id="${id}"]`);
          const pill = $(".status-pill", row);
          pill.className = "status-pill confirmed";
          pill.textContent = "Confirmed";
          row.classList.add("row-confirmed");
          btn.replaceWith(document.createTextNode("—"));
          updatePendingCount(-1);
          showToast("Delivery confirmed. Allocation marked received.");
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = "Confirm received";
        showToast("Could not confirm — try again.");
      }
    });
  });
}

function updatePendingCount(delta) {
  const badge = $("#navPendingBadge");
  const count = $("#pendingCount");
  let n = badge ? Number(badge.textContent) : 0;
  n = Math.max(0, n + delta);
  if (badge) { badge.textContent = String(n); if (n === 0) badge.style.display = "none"; }
  if (count) count.textContent = n === 0 ? "all confirmed" : `${n} pending`;
}

/* ---------- toast ---------- */
let toastTimer;
function showToast(msg) {
  const t = $("#toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
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

  // mobile drawer
  const backdrop = document.createElement("div");
  backdrop.className = "backdrop";
  document.body.appendChild(backdrop);
  const openMobile = () => { sidebar.classList.add("open"); backdrop.classList.add("show"); };
  const closeMobile = () => { sidebar.classList.remove("open"); backdrop.classList.remove("show"); };
  if (menuToggle) menuToggle.addEventListener("click", openMobile);
  backdrop.addEventListener("click", closeMobile);
  $$(".side-link").forEach((l) => l.addEventListener("click", () => { if (window.innerWidth <= 820) closeMobile(); }));
}

/* ---------- theme toggle (light default, remembered) ---------- */
function initTheme() {
  const btn = $("#themeToggle");
  if (!btn) return;
  const apply = (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("freshlink-theme", theme); } catch (e) {}
  };
  btn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    apply(current === "light" ? "dark" : "light");
  });
}

/* ---------- boot ---------- */
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initGreetingAndDate();
  initSidebar();
  initCounts();
  drawGauge();
  initConfirmButtons();
});