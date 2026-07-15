const $ = (selector, context = document) => context.querySelector(selector);
const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

function formatNumber(value) {
  return Number(value || 0).toLocaleString("en-US");
}

function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("en-GB", {
    day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
  });
}

function setText(selector, value) {
  const element = $(selector);
  if (element) element.textContent = value;
}

function showToast(message) {
  const toast = $("#toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3200);
}

function handleError(error, fallback) {
  if (error.status === 401) {
    window.location.assign(FreshLinkAPI.loginUrl);
    return;
  }
  showToast(error.message || fallback);
}

function initGreetingAndDate() {
  const hour = new Date().getHours();
  setText("#greeting", hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening");
  setText("#todayDate", new Date().toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  }));
}

function initTheme() {
  const button = $("#themeToggle");
  if (!button) return;
  button.addEventListener("click", () => {
    const next = (document.documentElement.getAttribute("data-theme") || "light") === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("freshlink-theme", next); } catch (error) {}
  });
}

function initSidebar() {
  const sidebar = $("#sidebar");
  if (!sidebar) return;
  const collapse = $("#sidebarCollapse");
  const menuToggle = $("#menuToggle");
  const resizeHandle = $("#resizeHandle");
  if (collapse) collapse.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
  try {
    const savedWidth = localStorage.getItem("freshlink-sidebar-w");
    if (savedWidth) document.documentElement.style.setProperty("--sb-w", `${savedWidth}px`);
  } catch (error) {}
  if (resizeHandle) {
    resizeHandle.addEventListener("mousedown", (event) => {
      if (sidebar.classList.contains("collapsed")) return;
      const resize = (moveEvent) => {
        const width = Math.max(200, Math.min(420, moveEvent.clientX));
        document.documentElement.style.setProperty("--sb-w", `${width}px`);
      };
      const stop = () => {
        const width = getComputedStyle(document.documentElement).getPropertyValue("--sb-w").trim().replace("px", "");
        try { localStorage.setItem("freshlink-sidebar-w", width); } catch (error) {}
        window.removeEventListener("mousemove", resize);
        window.removeEventListener("mouseup", stop);
      };
      event.preventDefault();
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stop);
    });
  }
  const backdrop = document.createElement("div");
  backdrop.className = "backdrop";
  document.body.appendChild(backdrop);
  const close = () => {
    sidebar.classList.remove("open");
    backdrop.classList.remove("show");
  };
  if (menuToggle) menuToggle.addEventListener("click", () => {
    sidebar.classList.add("open");
    backdrop.classList.add("show");
  });
  backdrop.addEventListener("click", close);
  $$(".side-link").forEach((link) => link.addEventListener("click", () => {
    if (window.innerWidth <= 820) close();
  }));
}

function updateGauge(available, total) {
  const gauge = $("#capacityGauge");
  if (!gauge) return;
  const percentage = total ? Math.round((available / total) * 100) : 0;
  const fill = $(".gauge-fill", gauge);
  const circumference = 2 * Math.PI * 52;
  fill.style.stroke = percentage <= 20 ? "#d64545" : percentage <= 45 ? "#d97706" : "#1f7a4d";
  fill.style.strokeDashoffset = String(circumference - (percentage / 100) * circumference);
  setText("#gaugePct", `${percentage}%`);
  setText("#gaugeAvail", formatNumber(available));
  setText("#gaugeTotal", formatNumber(total));
  setText("#availPct", `${percentage}% free`);
}

function tableMessage(message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 5;
  cell.className = "table-message";
  cell.textContent = message;
  row.appendChild(cell);
  return row;
}

function renderAllocations(allocations) {
  const body = $("#allocations-body");
  if (!body) return;
  body.replaceChildren();
  if (!allocations.length) {
    body.appendChild(tableMessage("No allocations have been sent to this hub yet."));
    return;
  }
  allocations.forEach((allocation) => {
    const row = document.createElement("tr");
    const farmer = document.createElement("td");
    farmer.textContent = allocation.farmer || "Farmer details unavailable";
    const quantity = document.createElement("td");
    quantity.textContent = `${formatNumber(allocation.received_quantity_kg || allocation.total_load_kg)} kg`;
    const pickup = document.createElement("td");
    pickup.textContent = formatDateTime(allocation.pickup_start);
    const status = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `status-pill ${allocation.receipt_status === "CONFIRMED" ? "confirmed" : "pending"}`;
    pill.textContent = allocation.receipt_status === "CONFIRMED" ? "Confirmed" : "Pending";
    status.appendChild(pill);
    const action = document.createElement("td");
    if (allocation.receipt_status === "PENDING") {
      const button = document.createElement("button");
      button.className = "btn btn-confirm";
      button.type = "button";
      button.dataset.allocationId = allocation.allocation_id;
      button.textContent = "Confirm received";
      action.appendChild(button);
    } else {
      action.textContent = "—";
    }
    row.append(farmer, quantity, pickup, status, action);
    body.appendChild(row);
  });
}

function setHubStatus(hub) {
  const status = $("#hub-status");
  if (!status) return;
  status.replaceChildren();
  const dot = document.createElement("span");
  dot.className = hub.accepting_deliveries ? "dot ok" : "dot";
  status.append(dot, ` ${hub.accepting_deliveries ? "Accepting deliveries" : "Not accepting deliveries"}`);
}

async function loadDashboard() {
  try {
    const [dashboard, allocations] = await Promise.all([
      FreshLinkAPI.request("/api/hub/dashboard"),
      FreshLinkAPI.request("/api/hub/allocations?page_size=100"),
    ]);
    const hub = dashboard.hub;
    setText("#hub-heading", hub.name);
    setText("#sidebar-hub-name", hub.name);
    setText("#available-capacity", formatNumber(hub.available_capacity_kg));
    setText("#total-capacity", formatNumber(hub.total_capacity_kg));
    setText("#pending-allocations", dashboard.statistics.pending_allocations === null ? "—" : formatNumber(dashboard.statistics.pending_allocations));
    setText("#confirmed-today", formatNumber(dashboard.statistics.confirmed_today));
    const pending = dashboard.statistics.pending_allocations || 0;
    setText("#navPendingBadge", formatNumber(pending));
    setText("#pendingCount", dashboard.coordination_data_available ? `${pending} pending` : "No engine allocations yet");
    setText("#profile-hub-name", hub.name);
    setText("#profile-capacity", `${formatNumber(hub.available_capacity_kg)} / ${formatNumber(hub.total_capacity_kg)} kg`);
    setText("#profile-status", hub.accepting_deliveries ? "Accepting deliveries" : "Not accepting deliveries");
    setHubStatus(hub);
    updateGauge(hub.available_capacity_kg, hub.total_capacity_kg);
    renderAllocations(allocations.items);
  } catch (error) {
    const body = $("#allocations-body");
    if (body) body.replaceChildren(tableMessage("Unable to load allocations."));
    handleError(error, "Unable to load hub data.");
  }
}

function initConfirmActions() {
  const table = $("#allocationsTable");
  if (!table) return;
  table.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-allocation-id]");
    if (!button) return;
    button.disabled = true;
    try {
      await FreshLinkAPI.request(`/api/hub/allocations/${button.dataset.allocationId}/confirm`, { method: "POST" });
      showToast("Delivery confirmed.");
      await loadDashboard();
    } catch (error) {
      handleError(error, "Unable to confirm this delivery.");
      button.disabled = false;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initGreetingAndDate();
  initSidebar();
  initConfirmActions();
  loadDashboard();
});
