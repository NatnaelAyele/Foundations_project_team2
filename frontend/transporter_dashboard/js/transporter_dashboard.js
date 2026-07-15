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

function initTheme() {
  const button = $("#themeToggle");
  if (!button) return;
  button.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("freshlink-theme", next); } catch (error) {}
  });
}

function initGreetingAndDate() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  setText("#greeting", greeting);
  setText("#todayDate", new Date().toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  }));
}

function initSidebar() {
  const sidebar = $("#sidebar");
  if (!sidebar) return;
  const collapse = $("#sidebarCollapse");
  const menuToggle = $("#menuToggle");
  if (collapse) collapse.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
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
  const gauge = $("#fleetGauge");
  if (!gauge) return;
  const percentage = total ? Math.round((available / total) * 100) : 0;
  const fill = $(".gauge-fill", gauge);
  const circumference = 2 * Math.PI * 52;
  fill.style.stroke = percentage <= 33 ? "#d64545" : percentage <= 66 ? "#d97706" : "#1f7a4d";
  fill.style.strokeDashoffset = String(circumference - (percentage / 100) * circumference);
  setText("#gaugePct", `${percentage}%`);
  setText("#gaugeAvail", formatNumber(available));
  setText("#gaugeTotal", formatNumber(total));
}

function setFleetStatus(available, total) {
  const status = $("#fleet-status");
  if (!status) return;
  status.replaceChildren();
  const dot = document.createElement("span");
  dot.className = available ? "dot ok" : "dot";
  status.append(dot, ` ${available} of ${total} trucks available`);
}

function statusPill(status) {
  const pill = document.createElement("span");
  const value = String(status || "").toUpperCase();
  const className = value === "ASSIGNED" ? "assigned" : value === "IN_TRANSIT" ? "active2" : "delivered";
  pill.className = `status-pill ${className}`;
  pill.textContent = value === "IN_TRANSIT" ? "In transit" : value.charAt(0) + value.slice(1).toLowerCase();
  return pill;
}

function tableMessage(message) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 6;
  cell.className = "table-message";
  cell.textContent = message;
  row.appendChild(cell);
  return row;
}

function renderTrips(trips) {
  const body = $("#trips-body");
  if (!body) return;
  body.replaceChildren();
  if (!trips.length) {
    body.appendChild(tableMessage("No trips have been assigned yet."));
    return;
  }
  trips.forEach((trip) => {
    const row = document.createElement("tr");
    const pickup = document.createElement("td");
    pickup.textContent = `${trip.pickup_location.village || trip.pickup_location.sector} · ${formatDateTime(trip.pickup_start)}`;
    const load = document.createElement("td");
    load.textContent = `${formatNumber(trip.total_load_kg)} kg`;
    const destination = document.createElement("td");
    destination.textContent = trip.destination_hub.name;
    const truck = document.createElement("td");
    truck.textContent = trip.truck.plate_number;
    const status = document.createElement("td");
    status.appendChild(statusPill(trip.status));
    const actions = document.createElement("td");
    if (trip.status === "ASSIGNED" || trip.status === "IN_TRANSIT") {
      const button = document.createElement("button");
      button.className = "btn btn-start";
      button.dataset.action = trip.status === "ASSIGNED" ? "start" : "deliver";
      button.dataset.allocationId = trip.allocation_id;
      button.textContent = trip.status === "ASSIGNED" ? "Start pickup" : "Mark delivered";
      actions.appendChild(button);
    } else {
      actions.textContent = "—";
    }
    row.append(pickup, load, destination, truck, status, actions);
    body.appendChild(row);
  });
}

function truckState(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "AVAILABLE") return { label: "Available", enabled: true };
  if (normalized === "MAINTENANCE") return { label: "Maintenance", enabled: true };
  if (normalized === "EN_ROUTE") return { label: "En route", enabled: false };
  return { label: "Full", enabled: false };
}

function renderTrucks(trucks) {
  const list = $("#truckList");
  if (!list) return;
  list.replaceChildren();
  if (!trucks.length) {
    const message = document.createElement("p");
    message.className = "hint";
    message.textContent = "No trucks are registered. Use the truck status page to add one.";
    list.appendChild(message);
    return;
  }
  trucks.forEach((truck) => {
    const state = truckState(truck.status);
    const row = document.createElement("div");
    row.className = "truck-row";
    const plate = document.createElement("span");
    plate.className = "truck-plate";
    plate.textContent = truck.plate_number;
    const meta = document.createElement("span");
    meta.className = "truck-meta";
    const model = document.createElement("b");
    model.textContent = truck.vehicle_model || "Truck";
    const capacity = document.createElement("span");
    capacity.textContent = `Capacity ${formatNumber(truck.capacity_kg)} kg`;
    meta.append(model, capacity);
    const status = document.createElement("span");
    status.className = `avail-state ${truck.status === "AVAILABLE" ? "on" : "off"}`;
    status.textContent = state.label;
    const toggle = document.createElement("button");
    toggle.className = "avail-switch";
    toggle.type = "button";
    toggle.setAttribute("role", "switch");
    toggle.setAttribute("aria-checked", String(truck.status === "AVAILABLE"));
    toggle.setAttribute("aria-label", `Toggle availability for ${truck.plate_number}`);
    toggle.dataset.truckId = truck.truck_id;
    toggle.disabled = !state.enabled;
    toggle.title = state.enabled ? "Toggle availability" : "Update this truck from the truck status page";
    toggle.appendChild(document.createElement("span")).className = "knob";
    row.append(plate, meta, status, toggle);
    list.appendChild(row);
  });
}

async function loadDashboard() {
  try {
    const [dashboard, trips, trucks] = await Promise.all([
      FreshLinkAPI.request("/api/transporter/dashboard"),
      FreshLinkAPI.request("/api/transporter/trips?page_size=100"),
      FreshLinkAPI.request("/api/transporter/trucks"),
    ]);
    const profile = dashboard.transporter;
    const fleet = dashboard.fleet;
    setText("#transporter-heading", profile.name);
    setText("#sidebar-transporter-name", profile.name);
    setText("#assigned-trips-count", dashboard.trips.awaiting_pickup === null ? "—" : formatNumber(dashboard.trips.awaiting_pickup));
    setText("#available-trucks-count", formatNumber(fleet.available_trucks));
    setText("#total-trucks-count", `/ ${formatNumber(fleet.total_trucks)}`);
    setText("#available-capacity-count", formatNumber(fleet.available_capacity_kg));
    setText("#delivered-today-count", formatNumber(dashboard.trips.delivered_today));
    setText("#assignedNote", dashboard.coordination_data_available ? "awaiting pickup" : "engine trips unavailable");
    const awaiting = dashboard.trips.awaiting_pickup || 0;
    setText("#navTripBadge", formatNumber(awaiting));
    setText("#tripCount", dashboard.coordination_data_available ? `${awaiting} to pick up` : "No engine trips yet");
    setFleetStatus(fleet.available_trucks, fleet.total_trucks);
    updateGauge(fleet.available_trucks, fleet.total_trucks);
    setText("#profile-name", profile.name);
    setText("#profile-sector", `${profile.base_sector}, ${profile.district}`);
    setText("#profile-fleet", `${fleet.total_trucks} trucks (${formatNumber(fleet.total_capacity_kg)} kg)`);
    setText("#profile-status", fleet.accepting_trips ? "Accepting trips" : "No trucks available");
    renderTrips(trips.items);
    renderTrucks(trucks.items);
  } catch (error) {
    const tripsBody = $("#trips-body");
    if (tripsBody) tripsBody.replaceChildren(tableMessage("Unable to load trips."));
    const trucks = $("#truckList");
    if (trucks) trucks.textContent = "Unable to load trucks.";
    handleError(error, "Unable to load transporter data.");
  }
}

function initTripActions() {
  const table = $("#tripsTable");
  if (!table) return;
  table.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    button.disabled = true;
    try {
      await FreshLinkAPI.request(`/api/transporter/trips/${button.dataset.allocationId}/${action === "start" ? "start" : "deliver"}`, { method: "POST" });
      showToast(action === "start" ? "Pickup started." : "Trip marked delivered.");
      await loadDashboard();
    } catch (error) {
      handleError(error, "Unable to update this trip.");
      button.disabled = false;
    }
  });
}

function initTruckToggles() {
  const list = $("#truckList");
  if (!list) return;
  list.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-truck-id]");
    if (!button || button.disabled) return;
    const available = button.getAttribute("aria-checked") !== "true";
    button.disabled = true;
    try {
      await FreshLinkAPI.request(`/api/transporter/trucks/${button.dataset.truckId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: available ? "AVAILABLE" : "MAINTENANCE" }),
      });
      showToast(`Truck marked ${available ? "available" : "under maintenance"}.`);
      await loadDashboard();
    } catch (error) {
      handleError(error, "Unable to update truck availability.");
      button.disabled = false;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initGreetingAndDate();
  initSidebar();
  initTripActions();
  initTruckToggles();
  loadDashboard();
});
