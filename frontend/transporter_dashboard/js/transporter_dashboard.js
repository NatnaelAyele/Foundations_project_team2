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
  // POST /api/trucks                          → insert into trucks (plate_number, capacity_kg, transporter_id)
  async addTruck(truck) { return { ok: true, truck }; },
  // DELETE /api/trucks/{plate}                → delete from trucks
  async removeTruck(plate) { return { ok: true, plate }; },
  // GET /api/transporters/{id}/trucks         → load the fleet on page load
  async getTrucks() { return null; },
};

/* ---------- trip data (swap for TransporterAPI.getTrips() when backend is live) ----------
   Comes from trip_allocations joined with farmers + cold_hubs + trucks.
   status: assigned | in_transit | delivered
--------------------------------------------------------------------------------- */
let TRIPS = [
  { id: "1", pickup: "Kavumu", when: "Today 2:00 PM", load: 220, hub: "Kamonyi Central", truck: "RAD 221 A", status: "assigned" },
  { id: "2", pickup: "Gahogo", when: "Today 4:30 PM", load: 150, hub: "Kamonyi Central", truck: "RAD 118 B", status: "assigned" },
  { id: "3", pickup: "Nyagisozi", when: "Today 11:00 AM", load: 310, hub: "Rukoma Cold Storage", truck: "RAD 221 A", status: "in_transit" },
  { id: "4", pickup: "Kabuye", when: "Yesterday 3:15 PM", load: 180, hub: "Kamonyi Central", truck: "RAD 118 B", status: "delivered" },
];

/* ---------- truck data (swap for TransporterAPI.getTrucks() when backend is live) ---------- */
let TRUCKS = [
  { plate: "RAD 221 A", model: "Isuzu ELF", capacity: 500, available: true },
  { plate: "RAD 118 B", model: "Toyota Dyna", capacity: 400, available: true },
  { plate: "RAD 904 C", model: "Mitsubishi Canter", capacity: 350, available: false },
];

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

/* ---------- trips: render + actions (assigned → in_transit → delivered) ---------- */
const TRIP_UI = {
  assigned:   { pill: "assigned",  label: "Assigned",   action: "start",   btn: "Start pickup" },
  in_transit: { pill: "active2",   label: "In transit", action: "deliver", btn: "Mark delivered" },
  delivered:  { pill: "delivered", label: "Delivered",  action: null,      btn: null },
};

function renderTrips() {
  const body = $("#tripsBody");
  if (!body) return;

  body.innerHTML = TRIPS.map((t) => {
    const ui = TRIP_UI[t.status] || TRIP_UI.assigned;
    const actionCell = ui.action
      ? `<div class="trip-actions"><button class="btn btn-start" data-action="${ui.action}" data-row-id="${t.id}">${ui.btn}</button></div>`
      : "&mdash;";
    return `
      <tr data-row-id="${t.id}">
        <td>${t.pickup} &middot; ${t.when}</td>
        <td>${t.load} kg</td>
        <td>${t.hub}</td>
        <td>${t.truck}</td>
        <td><span class="status-pill ${ui.pill}">${ui.label}</span></td>
        <td>${actionCell}</td>
      </tr>`;
  }).join("");

  const empty = $("#tripsEmpty");
  if (empty) empty.style.display = TRIPS.length ? "none" : "block";

  bindTripActions();
  recomputeTrips();
}

function bindTripActions() {
  $$('#tripsTable .btn[data-action]').forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.rowId;
      const action = btn.dataset.action;
      const trip = TRIPS.find((t) => t.id === id);
      if (!trip) return;

      btn.disabled = true;
      btn.textContent = "…";
      try {
        if (action === "start") {
          await TransporterAPI.startTrip(id);
          trip.status = "in_transit";
          renderTrips();
          showToast("Pickup started — trip is in transit.");
        } else {
          await TransporterAPI.deliverTrip(id);
          trip.status = "delivered";
          renderTrips();
          const row = $(`#tripsTable tr[data-row-id="${id}"]`);
          if (row) row.classList.add("row-confirmed");
          showToast("Trip marked delivered.");
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = action === "start" ? "Start pickup" : "Mark delivered";
        showToast("Could not update — try again.");
      }
    });
  });
}

/* keep the badge, the panel count and the hero stats honest */
function recomputeTrips() {
  const toPickUp = TRIPS.filter((t) => t.status === "assigned").length;
  const deliveredToday = TRIPS.filter((t) => t.status === "delivered").length;

  const badge = $("#navTripBadge");
  if (badge) {
    badge.textContent = String(toPickUp);
    badge.style.display = toPickUp === 0 ? "none" : "";
  }
  const count = $("#tripCount");
  if (count) count.textContent = toPickUp === 0 ? "all picked up" : `${toPickUp} to pick up`;

  const counts = $$(".hero-stats .count");
  if (counts[0]) { counts[0].dataset.target = toPickUp; counts[0].textContent = toPickUp; }
  if (counts[3]) { counts[3].dataset.target = deliveredToday; counts[3].textContent = deliveredToday; }
}

/* ---------- trucks: render / register / remove / availability ---------- */
function renderTrucks() {
  const list = $("#truckList");
  if (!list) return;
  list.innerHTML = TRUCKS.map((t) => `
    <div class="truck-row" data-truck="${t.plate}">
      <span class="truck-plate">${t.plate}</span>
      <span class="truck-meta"><b>${t.model}</b><span>Capacity ${t.capacity} kg</span></span>
      <span class="avail-state ${t.available ? "on" : "off"}">${t.available ? "Available" : "Not available"}</span>
      <button class="avail-switch" role="switch" aria-checked="${t.available}" aria-label="Toggle availability for ${t.plate}"><span class="knob"></span></button>
      <button class="btn btn-outline remove-truck" type="button" data-plate="${t.plate}" aria-label="Remove ${t.plate}">Remove</button>
    </div>`).join("");

  const empty = $("#truckEmpty");
  if (empty) empty.style.display = TRUCKS.length ? "none" : "block";
  const count = $("#truckCount");
  if (count) count.textContent = TRUCKS.length === 1 ? "1 truck" : `${TRUCKS.length} trucks`;

  bindTruckRowEvents();
  recomputeFleet();
}

function bindTruckRowEvents() {
  $$(".avail-switch").forEach((sw) => {
    sw.addEventListener("click", async () => {
      const row = sw.closest(".truck-row");
      const plate = row.dataset.truck;
      const truck = TRUCKS.find((t) => t.plate === plate);
      if (!truck) return;
      const nowOn = !truck.available;
      truck.available = nowOn;
      sw.setAttribute("aria-checked", String(nowOn));
      const state = $(".avail-state", row);
      state.textContent = nowOn ? "Available" : "Not available";
      state.className = "avail-state " + (nowOn ? "on" : "off");
      try {
        await TransporterAPI.setTruckAvailability(plate, nowOn);
        recomputeFleet();
        showToast(`${plate} is now ${nowOn ? "available" : "not available"}.`);
      } catch (err) {
        truck.available = !nowOn;
        renderTrucks();
        showToast("Could not update truck — try again.");
      }
    });
  });

  $$(".remove-truck").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const plate = btn.dataset.plate;
      if (!confirm(`Remove ${plate} from your fleet?`)) return;
      btn.disabled = true;
      try {
        await TransporterAPI.removeTruck(plate);
        TRUCKS = TRUCKS.filter((t) => t.plate !== plate);
        renderTrucks();
        showToast(`${plate} removed from your fleet.`);
      } catch (err) {
        btn.disabled = false;
        showToast("Could not remove truck — try again.");
      }
    });
  });
}

function initAddTruck() {
  const btn = $("#addTruckBtn");
  if (!btn) return;
  const submit = async () => {
    const plateEl = $("#newPlate"), modelEl = $("#newModel"), capEl = $("#newCapacity");
    const plate = plateEl.value.trim().toUpperCase();
    const model = modelEl.value.trim();
    const capacity = Number(capEl.value);
    if (!plate) { showToast("Enter a plate number."); plateEl.focus(); return; }
    if (!model) { showToast("Enter the truck model."); modelEl.focus(); return; }
    if (!capacity || capacity <= 0) { showToast("Enter a capacity in kg."); capEl.focus(); return; }
    if (TRUCKS.some((t) => t.plate === plate)) { showToast(`${plate} is already registered.`); plateEl.focus(); return; }
    const truck = { plate, model, capacity, available: true };
    btn.disabled = true; btn.textContent = "Saving…";
    try {
      await TransporterAPI.addTruck(truck);
      TRUCKS.push(truck);
      renderTrucks();
      plateEl.value = ""; modelEl.value = ""; capEl.value = "";
      showToast(`${plate} registered and marked available.`);
    } catch (err) {
      showToast("Could not register truck — try again.");
    } finally {
      btn.disabled = false; btn.textContent = "Register truck";
    }
  };
  btn.addEventListener("click", submit);
  ["#newPlate", "#newModel", "#newCapacity"].forEach((sel) => {
    const el = $(sel);
    if (el) el.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  });
}

function recomputeFleet() {
  const total = TRUCKS.length;
  const avail = TRUCKS.filter((t) => t.available).length;
  const availKg = TRUCKS.filter((t) => t.available).reduce((s, t) => s + t.capacity, 0);

  const gauge = $("#fleetGauge");
  if (gauge) { gauge.dataset.available = avail; gauge.dataset.total = total || 1; drawGauge(); }
  const ga = $("#gaugeAvail"); if (ga) ga.textContent = avail;
  const gt = $("#gaugeTotal"); if (gt) gt.textContent = total;

  const tag = $(".hub-tag-value");
  if (tag) tag.innerHTML = `<span class="dot ok"></span> ${avail} truck${avail === 1 ? "" : "s"} available`;

  const counts = $$(".hero-stats .count");
  if (counts[1]) { counts[1].dataset.target = avail; counts[1].textContent = avail; }
  const unitEl = $(".stripe-lightgreen .stat-unit");
  if (unitEl) unitEl.textContent = "/ " + total;
  if (counts[2]) { counts[2].dataset.target = availKg; counts[2].textContent = availKg.toLocaleString("en-US"); }

  const fleetVals = $$(".hd-value");
  if (fleetVals[2]) {
    const totalKg = TRUCKS.reduce((s, t) => s + t.capacity, 0);
    fleetVals[2].textContent = `${total} truck${total === 1 ? "" : "s"} (${totalKg.toLocaleString("en-US")} kg)`;
  }
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

  // restore saved width
  try {
    const savedW = localStorage.getItem("freshlink-sidebar-w");
    if (savedW) document.documentElement.style.setProperty("--sb-w", savedW + "px");
  } catch (e) {}
  // drag-to-resize
  const handle = document.querySelector("#resizeHandle");
  if (handle) {
    let dragging = false;
    const MIN = 200, MAX = 420;
    const onMove = (e) => { if (!dragging) return; const w = Math.max(MIN, Math.min(MAX, e.clientX)); document.documentElement.style.setProperty("--sb-w", w + "px"); };
    const stop = () => { if (!dragging) return; dragging = false; handle.classList.remove("dragging"); document.body.classList.remove("resizing"); const w = getComputedStyle(document.documentElement).getPropertyValue("--sb-w").trim().replace("px",""); try { localStorage.setItem("freshlink-sidebar-w", w); } catch (e) {} window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", stop); };
    handle.addEventListener("mousedown", (e) => { if (sidebar.classList.contains("collapsed")) return; dragging = true; handle.classList.add("dragging"); document.body.classList.add("resizing"); e.preventDefault(); window.addEventListener("mousemove", onMove); window.addEventListener("mouseup", stop); });
    handle.addEventListener("dblclick", () => { document.documentElement.style.setProperty("--sb-w","256px"); try { localStorage.setItem("freshlink-sidebar-w","256"); } catch (e) {} });
  }

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
  renderTrips();
  renderTrucks();
  initAddTruck();
});