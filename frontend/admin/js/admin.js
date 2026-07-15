const $ = (selector, context = document) => context.querySelector(selector);
const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

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

function initSidebar() {
  const sidebar = $("#sidebar");
  const collapse = $("#sidebarCollapse");
  const menuToggle = $("#menuToggle");
  if (!sidebar) return;

  if (collapse) collapse.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
  const backdrop = document.createElement("div");
  backdrop.className = "backdrop";
  document.body.appendChild(backdrop);

  const close = () => {
    sidebar.classList.remove("open");
    backdrop.classList.remove("show");
  };
  if (menuToggle) {
    menuToggle.addEventListener("click", () => {
      sidebar.classList.add("open");
      backdrop.classList.add("show");
    });
  }
  backdrop.addEventListener("click", close);
  $$(".side-link").forEach((link) => link.addEventListener("click", () => {
    if (window.innerWidth <= 820) close();
  }));
}

function initGreetingAndDate() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const greetingElement = $("#greeting");
  const dateElement = $("#todayDate");
  if (greetingElement) greetingElement.textContent = `${greeting}, Admin`;
  if (dateElement) {
    dateElement.textContent = new Date().toLocaleDateString("en-GB", {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    });
  }
}

function setText(selector, value) {
  const element = $(selector);
  if (element) element.textContent = value;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("en-US");
}

function formatKilograms(value) {
  return `${formatNumber(value)} kg`;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function statusLabel(value) {
  return String(value || "Unknown").replaceAll("_", " ").toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "active") return "status-active";
  if (normalized.includes("pending")) return "status-pending";
  if (normalized.includes("confirm")) return "status-confirmed";
  if (normalized.includes("plan")) return "status-planned";
  return "status-new";
}

function statusPill(value) {
  const pill = document.createElement("span");
  pill.className = `status-pill ${statusClass(value)}`;
  pill.textContent = statusLabel(value);
  return pill;
}

function setTableMessage(body, columns, message) {
  body.replaceChildren();
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = columns;
  cell.className = "table-message";
  cell.textContent = message;
  row.appendChild(cell);
  body.appendChild(row);
}

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value || "—";
  row.appendChild(cell);
  return cell;
}

function showToast(message) {
  const toast = $("#toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3500);
}

function handleApiError(error, fallback) {
  if (error.status === 401) {
    window.location.assign(FreshLinkAPI.loginUrl);
    return;
  }
  showToast(error.message || fallback);
}

function validateForm(form) {
  let valid = true;
  $$("input[required], select[required], textarea[required]", form).forEach((field) => {
    const hasValue = field.type === "radio" ? true : field.value.trim() !== "";
    if (field.type !== "radio") {
      field.closest(".field")?.classList.toggle("error", !hasValue);
      if (!hasValue) valid = false;
    }
  });

  [...new Set($$("input[type='radio'][required]", form).map((field) => field.name))]
    .forEach((name) => {
      const fields = $$(`input[name="${name}"]`, form);
      const selected = fields.some((field) => field.checked);
      fields[0]?.closest(".field")?.classList.toggle("error", !selected);
      if (!selected) valid = false;
    });
  return valid;
}

function watchFormFields(form) {
  $$("input, select, textarea", form).forEach((field) => {
    const clearError = () => field.closest(".field")?.classList.remove("error");
    field.addEventListener("input", clearError);
    field.addEventListener("change", clearError);
  });
}

async function loadDashboard() {
  const farmerBody = $("#recent-farmers-body");
  if (!farmerBody) return;
  const forecastBody = $("#recent-forecasts-body");

  try {
    const summary = await FreshLinkAPI.request("/api/admin/dashboard/summary");
    setText("#farmer-total", formatNumber(summary.farmers.total));
    setText("#forecast-total", formatNumber(summary.forecasts.total));
    setText("#transport-needed", formatNumber(summary.forecasts.needing_transport));
    setText("#storage-needed", formatNumber(summary.forecasts.needing_storage));
    setText("#farmers-week-note", `+${formatNumber(summary.farmers.registered_this_week)} this week`);
    setText("#forecasts-week-note", `+${formatNumber(summary.forecasts.submitted_this_week)} this week`);

    const status = $("#engine-status");
    if (status) {
      status.replaceChildren();
      const dot = document.createElement("span");
      dot.className = `dot ${summary.engine.available ? "ok" : ""}`;
      status.append(dot, ` ${summary.engine.available ? "Engine available" : "Engine unavailable"}`);
      status.title = summary.engine.message;
    }

    renderRecentFarmers(farmerBody, summary.recent_farmers);
    renderRecentForecasts(forecastBody, summary.recent_forecasts);
  } catch (error) {
    setTableMessage(farmerBody, 5, "Unable to load recent farmers.");
    if (forecastBody) setTableMessage(forecastBody, 5, "Unable to load recent forecasts.");
    handleApiError(error, "Unable to load dashboard data.");
  }
}

function renderRecentFarmers(body, farmers) {
  if (!farmers.length) return setTableMessage(body, 5, "No farmers have been registered yet.");
  body.replaceChildren();
  farmers.forEach((farmer) => {
    const row = document.createElement("tr");
    addCell(row, farmer.name);
    addCell(row, farmer.sector);
    addCell(row, farmer.village);
    addCell(row, farmer.phone);
    const statusCell = document.createElement("td");
    statusCell.appendChild(statusPill(farmer.status));
    row.appendChild(statusCell);
    body.appendChild(row);
  });
}

function renderRecentForecasts(body, forecasts) {
  if (!forecasts.length) return setTableMessage(body, 5, "No forecasts have been submitted yet.");
  body.replaceChildren();
  forecasts.forEach((forecast) => {
    const row = document.createElement("tr");
    addCell(row, forecast.farmer_name);
    addCell(row, formatDate(forecast.harvest_date));
    addCell(row, formatKilograms(forecast.quantity_kg));
    addCell(row, forecast.needs_transport ? "Yes" : "No").className = forecast.needs_transport ? "tag-yes" : "tag-no";
    addCell(row, forecast.needs_storage ? "Yes" : "No").className = forecast.needs_storage ? "tag-yes" : "tag-no";
    body.appendChild(row);
  });
}

async function loadSectors(select) {
  try {
    const result = await FreshLinkAPI.request("/api/admin/sectors?district=Kamonyi");
    select.replaceChildren(new Option("Select sector", "", true, true));
    select.options[0].disabled = true;
    result.items.forEach((sector) => select.add(new Option(sector.name, sector.name)));
  } catch (error) {
    select.replaceChildren(new Option("Unable to load sectors", "", true, true));
    select.options[0].disabled = true;
    handleApiError(error, "Unable to load sectors.");
  }
}

function initFarmerForm() {
  const form = $("#register-farmer-form");
  if (!form) return;
  const sectorSelect = $("#rf-sector", form);
  loadSectors(sectorSelect);
  watchFormFields(form);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateForm(form)) return;
    const submit = $("button[type='submit']", form);
    submit.disabled = true;
    FreshLinkAPI.setFormNotice(form, "Registering farmer…", "loading");
    try {
      const data = Object.fromEntries(new FormData(form));
      const farmer = await FreshLinkAPI.request("/api/admin/farmers", {
        method: "POST",
        body: JSON.stringify(data),
      });
      form.reset();
      const success = $("#register-success");
      if (success) success.classList.add("show");
      FreshLinkAPI.setFormNotice(form, `${farmer.name} was registered successfully.`, "success");
      showToast("Farmer registered.");
    } catch (error) {
      FreshLinkAPI.setFormNotice(form, error.message || "Unable to register farmer.", "error");
      handleApiError(error, "Unable to register farmer.");
    } finally {
      submit.disabled = false;
    }
  });
}

function initFarmerList() {
  const body = $("#farmer-table-body");
  const input = $("#farmer-search");
  if (!body || !input) return;
  let searchTimer;
  const load = async () => {
    setTableMessage(body, 6, "Loading farmers…");
    try {
      const query = new URLSearchParams({ page_size: "100" });
      if (input.value.trim()) query.set("search", input.value.trim());
      const result = await FreshLinkAPI.request(`/api/admin/farmers?${query}`);
      renderFarmers(body, result.items);
      $("#farmer-no-results").style.display = "none";
    } catch (error) {
      setTableMessage(body, 6, "Unable to load farmers.");
      handleApiError(error, "Unable to load farmers.");
    }
  };
  input.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(load, 250);
  });
  load();
}

function renderFarmers(body, farmers) {
  if (!farmers.length) return setTableMessage(body, 6, "No farmers match your search.");
  body.replaceChildren();
  farmers.forEach((farmer) => {
    const row = document.createElement("tr");
    [farmer.name, farmer.sector, farmer.cell, farmer.village, farmer.phone].forEach((value) => addCell(row, value));
    const statusCell = document.createElement("td");
    statusCell.appendChild(statusPill(farmer.status));
    row.appendChild(statusCell);
    body.appendChild(row);
  });
}

async function loadFarmerOptions(select) {
  try {
    const result = await FreshLinkAPI.request("/api/admin/farmers?page_size=100");
    select.replaceChildren(new Option("Select a registered farmer", "", true, true));
    select.options[0].disabled = true;
    result.items.forEach((farmer) => {
      select.add(new Option(`${farmer.name} — ${farmer.sector}`, farmer.farmer_id));
    });
  } catch (error) {
    select.replaceChildren(new Option("Unable to load farmers", "", true, true));
    select.options[0].disabled = true;
    handleApiError(error, "Unable to load registered farmers.");
  }
}

function initForecastForm() {
  const form = $("#forecast-form");
  if (!form) return;
  loadFarmerOptions($("#fc-farmer", form));
  watchFormFields(form);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateForm(form)) return;
    const submit = $("button[type='submit']", form);
    submit.disabled = true;
    FreshLinkAPI.setFormNotice(form, "Saving forecast…", "loading");
    try {
      const fields = new FormData(form);
      const forecast = await FreshLinkAPI.request("/api/admin/forecasts", {
        method: "POST",
        body: JSON.stringify({
          farmer_id: Number(fields.get("farmer_id")),
          quantity_kg: Number(fields.get("quantity_kg")),
          harvest_date: fields.get("harvest_date"),
          needs_transport: fields.get("needs_transport") === "yes",
          needs_storage: fields.get("needs_storage") === "yes",
          notes: fields.get("notes")?.trim() || null,
        }),
      });
      form.reset();
      const success = $("#forecast-success");
      if (success) success.classList.add("show");
      FreshLinkAPI.setFormNotice(form, `Forecast for ${forecast.farmer_name} was saved.`, "success");
      showToast("Forecast saved.");
    } catch (error) {
      FreshLinkAPI.setFormNotice(form, error.message || "Unable to save forecast.", "error");
      handleApiError(error, "Unable to save forecast.");
    } finally {
      submit.disabled = false;
    }
  });
}

function initForecastList() {
  const body = $("#forecast-table-body");
  const input = $("#forecast-search");
  if (!body || !input) return;
  let searchTimer;
  const load = async () => {
    setTableMessage(body, 5, "Loading forecasts…");
    try {
      const query = new URLSearchParams({ page_size: "100" });
      if (input.value.trim()) query.set("search", input.value.trim());
      const result = await FreshLinkAPI.request(`/api/admin/forecasts?${query}`);
      renderForecasts(body, result.items);
      $("#forecast-no-results").style.display = "none";
    } catch (error) {
      setTableMessage(body, 5, "Unable to load forecasts.");
      handleApiError(error, "Unable to load forecasts.");
    }
  };
  input.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(load, 250);
  });
  load();
}

function renderForecasts(body, forecasts) {
  if (!forecasts.length) return setTableMessage(body, 5, "No forecasts match your search.");
  body.replaceChildren();
  forecasts.forEach((forecast) => {
    const row = document.createElement("tr");
    addCell(row, forecast.farmer_name);
    addCell(row, forecast.sector);
    addCell(row, formatDate(forecast.harvest_date));
    addCell(row, formatKilograms(forecast.quantity_kg));
    const statusCell = document.createElement("td");
    statusCell.appendChild(statusPill(forecast.status));
    row.appendChild(statusCell);
    body.appendChild(row);
  });
}

function createBarRow(label, value, maximum, className = "") {
  const row = document.createElement("div");
  row.className = "bar-row";
  const labelElement = document.createElement("span");
  labelElement.className = "bar-label";
  labelElement.textContent = label;
  const track = document.createElement("div");
  track.className = "bar-track";
  const fill = document.createElement("span");
  fill.className = `bar-fill ${className}`.trim();
  fill.style.width = `${maximum ? (value / maximum) * 100 : 0}%`;
  track.appendChild(fill);
  const valueElement = document.createElement("span");
  valueElement.className = "bar-value";
  valueElement.textContent = formatNumber(value);
  row.append(labelElement, track, valueElement);
  return row;
}

async function loadReports() {
  const sectorBars = $("#report-sector-bars");
  if (!sectorBars) return;
  try {
    const report = await FreshLinkAPI.request("/api/admin/reports");
    setText("#report-total-harvest", formatKilograms(report.total_harvest_kg));
    setText("#report-trips-coordinated", report.trips_coordinated === null ? "Unavailable" : formatNumber(report.trips_coordinated));
    setText("#report-matched", report.successfully_matched_percent === null ? "Unavailable" : `${formatNumber(report.successfully_matched_percent)}%`);
    setText("#report-excluded", report.excluded_unmatched === null ? "Unavailable" : formatNumber(report.excluded_unmatched));

    renderReportBars(sectorBars, report.harvest_by_sector, "No harvest forecasts fall within this month.", "quantity_kg");
    renderReportBars($("#report-exclusion-bars"), report.exclusion_reasons, "No engine coordination data is available yet.", "count", "accent");
    setText("#report-matching-note", report.matching_blocker || "");
  } catch (error) {
    sectorBars.textContent = "Unable to load report data.";
    const exclusions = $("#report-exclusion-bars");
    if (exclusions) exclusions.textContent = "Unable to load coordination data.";
    handleApiError(error, "Unable to load report data.");
  }
}

function renderReportBars(container, items, emptyMessage, valueKey, className = "") {
  if (!container) return;
  container.replaceChildren();
  if (!items.length) {
    const message = document.createElement("p");
    message.className = "hint";
    message.textContent = emptyMessage;
    container.appendChild(message);
    return;
  }
  const maximum = Math.max(...items.map((item) => Number(item[valueKey]) || 0));
  items.forEach((item, index) => {
    const rowClass = className || (index % 2 ? "secondary" : "");
    container.appendChild(createBarRow(item.sector || statusLabel(item.reason), Number(item[valueKey]), maximum, rowClass));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSidebar();
  initGreetingAndDate();
  loadDashboard();
  initFarmerForm();
  initFarmerList();
  initForecastForm();
  initForecastList();
  loadReports();
});
