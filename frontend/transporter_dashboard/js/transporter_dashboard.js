/* =====================================================================
   FreshLink — Transporter Dashboard
   Maps to real tables: trucks, trip_allocations, transporters, farmers.
   Replace the API stubs with FastAPI endpoints when the backend is ready.
   ===================================================================== */

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* ---------- API layer (stubs) ---------- */
const TransporterAPI = {
  // GET /api/transporters/{id}/trips
  async getTrips() { return null; }, // prototype uses server-rendered rows
  // POST /api/trips/{allocation_id}/start   → trip status: assigned → in_transit
  async startTrip(id) { return { ok: true, id }; },
  // POST /api/trips/{allocation_id}/deliver → trip status: in_transit → delivered
  async deliverTrip(id) { return { ok: true, id }; },
  // PATCH /api/trucks/{plate}/availability   → trucks.status available/offline
  async setTruckAvailability(plate, available) { return { ok: true, plate, available }; },
};

/* ---------- theme (light default, remembered) ---------- */
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

/* ---------- greeting + date ---------- */
function initGreetingAndDate() {
  const now = new Date();
  const h = now.getHours();
  const greet = h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
  const g = $("#greeting"); if (g) g.textContent = greet;
  const d = $("#todayDate");
  if (d) d.textContent = now.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}

/* ---------- count-up ---------- */
function animateCount(el) {
  const target = Number(el.dataset.target || "0");
  if (!target) { el.textContent = "0"; return; }
  const dur = 900, start = performance.now(), fmt = (n) => n.toLocaleString("en-US");
  function tick(now) {
    const p = Math.min((now - start) / dur, 1);
    el.textContent = fmt(Math.round(target * (1 - Math.pow(1 - p, 3))));
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
    entries.forEach((e) => { if (e.isIntersecting) { animateCount(e.target); io.unobserve(e.target); } });
  }, { threshold: 0.4 });
  $$(".count").forEach((el) => io.observe(el));
}

/* ---------- fleet gauge (available / total trucks) ---------- */
function drawGauge() {
  const gauge = $("#fleetGauge");
  if (!gauge) return;
  const avail = Number(gauge.dataset.available || 0);
  const total = Number(gauge.dataset.total || 1);
  const pct = total > 0 ? Math.round((avail / total) * 100) : 0;
  const fill = $(".gauge-fill", gauge);
  const circ = 2 * Math.PI * 52;
  fill.style.stroke = pct <= 33 ? "#d64545" : pct <= 66 ? "#d97706" : "#1f7a4d";
  requestAnimationFrame(() => { fill.style.strokeDashoffset = String(circ - (pct / 100) * circ); });
  const pctEl = $("#gaugePct");
  if (pctEl) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { pctEl.textContent = pct + "%"; }
    else {
      let cur = 0;
      const step = () => { cur += Math.max(1, Math.round(pct / 24)); if (cur >= pct) cur = pct; pctEl.textContent = cur + "%"; if (cur < pct) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }
  }
}

/* ---------- trip actions ---------- */
function initTripActions() {
  $$('#tripsTable .btn[data-action]').forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.rowId;
      const action = btn.dataset.action;
      const row = $(`#tripsTable tr[data-row-id="${id}"]`);
      const pill = $(".status-pill", row);
      btn.disabled = true; btn.textContent = "…";
      try {
        if (action === "start") {
          await TransporterAPI.startTrip(id);
          pill.className = "status-pill active2"; pill.textContent = "In transit";
          btn.textContent = "Mark delivered"; btn.dataset.action = "deliver"; btn.disabled = false;
          updateTripCount(-1);
          showToast("Pickup started — trip is in transit.");
        } else {
          await TransporterAPI.deliverTrip(id);
          pill.className = "status-pill delivered"; pill.textContent = "Delivered";
          row.classList.add("row-confirmed");
          const cell = btn.closest("td"); cell.textContent = "—";
          showToast("Trip marked delivered.");
        }
      } catch (err) {
        btn.disabled = false; btn.textContent = action === "start" ? "Start pickup" : "Mark delivered";
        showToast("Could not update — try again.");
      }
    });
  });
}
function updateTripCount(delta) {
  const badge = $("#navTripBadge"), count = $("#tripCount");
  let n = badge ? Number(badge.textContent) : 0;
  n = Math.max(0, n + delta);
  if (badge) { badge.textContent = String(n); if (n === 0) badge.style.display = "none"; }
  if (count) count.textContent = n === 0 ? "all picked up" : `${n} to pick up`;
}

/* ---------- truck availability switches ---------- */
function initTruckSwitches() {
  $$(".avail-switch").forEach((sw) => {
    sw.addEventListener("click", async () => {
      const row = sw.closest(".truck-row");
      const plate = row.dataset.truck;
      const nowOn = sw.getAttribute("aria-checked") !== "true";
      sw.setAttribute("aria-checked", String(nowOn));
      const state = $(".avail-state", row);
      state.textContent = nowOn ? "Available" : "Offline";
      state.className = "avail-state " + (nowOn ? "on" : "off");
      try {
        await TransporterAPI.setTruckAvailability(plate, nowOn);
        recomputeFleet();
        showToast(`${plate} is now ${nowOn ? "available" : "offline"}.`);
      } catch (err) {
        // revert on failure
        sw.setAttribute("aria-checked", String(!nowOn));
        state.textContent = !nowOn ? "Available" : "Offline";
        state.className = "avail-state " + (!nowOn ? "on" : "off");
        showToast("Could not update truck — try again.");
      }
    });
  });
}
function recomputeFleet() {
  const rows = $$(".truck-row");
  const total = rows.length;
  const avail = rows.filter((r) => $(".avail-switch", r).getAttribute("aria-checked") === "true").length;
  const gauge = $("#fleetGauge");
  if (gauge) { gauge.dataset.available = avail; gauge.dataset.total = total; drawGauge(); }
  const ga = $("#gaugeAvail"); if (ga) ga.textContent = avail;
  const gt = $("#gaugeTotal"); if (gt) gt.textContent = total;
  const tag = $(".hub-tag-value");
  if (tag) tag.innerHTML = `<span class="dot ok"></span> ${avail} truck${avail === 1 ? "" : "s"} available`;
}

/* ---------- toast ---------- */
let toastTimer;
function showToast(msg) {
  const t = $("#toast"); if (!t) return;
  t.textContent = msg; t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
}

/* ---------- sidebar ---------- */
function initSidebar() {
  const sidebar = $("#sidebar"), collapse = $("#sidebarCollapse"), menuToggle = $("#menuToggle");
  if (collapse) collapse.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
  const backdrop = document.createElement("div");
  backdrop.className = "backdrop"; document.body.appendChild(backdrop);
  const open = () => { sidebar.classList.add("open"); backdrop.classList.add("show"); };
  const close = () => { sidebar.classList.remove("open"); backdrop.classList.remove("show"); };
  if (menuToggle) menuToggle.addEventListener("click", open);
  backdrop.addEventListener("click", close);
  $$(".side-link").forEach((l) => l.addEventListener("click", () => { if (window.innerWidth <= 820) close(); }));
}

/* ---------- boot ---------- */
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initGreetingAndDate();
  initSidebar();
  initCounts();
  drawGauge();
  initTripActions();
  initTruckSwitches();
});