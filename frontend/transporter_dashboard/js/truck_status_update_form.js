const truckIdInput = document.getElementById("truckId");
const capacityInput = document.getElementById("capacity");
const statusSelect = document.getElementById("status");
const locationInput = document.getElementById("location");
const driverNameInput = document.getElementById("driverName");
const notesInput = document.getElementById("notes");
const form = document.getElementById("truckStatusForm");
const confirmBanner = document.getElementById("confirmBanner");
const existingTrucks = document.getElementById("existingTrucks");
const trucksByPlate = new Map();

const statusLabels = {
  available: "Available",
  "en-route": "En route",
  full: "Full",
  maintenance: "Maintenance",
};
const statusClasses = {
  available: "available",
  "en-route": "en-route",
  full: "full",
  maintenance: "maintenance",
};
const apiStatus = {
  available: "AVAILABLE",
  "en-route": "EN_ROUTE",
  full: "FULL",
  maintenance: "MAINTENANCE",
};

function normalizedPlate(value) {
  return value.trim().toUpperCase().replace(/\s+/g, " ");
}

function updatePreview() {
  document.getElementById("previewTruck").textContent = truckIdInput.value || "—";
  document.getElementById("previewCapacity").textContent = capacityInput.value
    ? `${Number(capacityInput.value).toLocaleString()} kg`
    : "—";
  document.getElementById("previewLocation").textContent = locationInput.value || "—";
  const previewStatus = document.getElementById("previewStatus");
  previewStatus.className = `status-pill ${statusClasses[statusSelect.value] || "limited"}`;
  previewStatus.textContent = statusLabels[statusSelect.value] || "Not set";
}

function setBanner(message, type) {
  confirmBanner.textContent = message;
  confirmBanner.classList.add("visible");
  confirmBanner.dataset.type = type;
}

function clearBanner() {
  confirmBanner.classList.remove("visible");
}

async function loadTrucks() {
  try {
    const result = await FreshLinkAPI.request("/api/transporter/trucks");
    trucksByPlate.clear();
    existingTrucks.replaceChildren();
    result.items.forEach((truck) => {
      trucksByPlate.set(normalizedPlate(truck.plate_number), truck);
      existingTrucks.appendChild(new Option(truck.plate_number, truck.plate_number));
    });
  } catch (error) {
    if (error.status === 401) window.location.assign(FreshLinkAPI.loginUrl);
    else setBanner(error.message || "Unable to load your trucks.", "error");
  }
}

function fillExistingTruck() {
  const truck = trucksByPlate.get(normalizedPlate(truckIdInput.value));
  if (!truck) return;
  truckIdInput.value = truck.plate_number;
  capacityInput.value = truck.capacity_kg;
  driverNameInput.value = truck.driver_name || "";
  locationInput.value = truck.current_location || "";
  notesInput.value = truck.notes || "";
  statusSelect.value = Object.entries(apiStatus).find(([, value]) => value === truck.status)?.[0] || "";
  updatePreview();
}

async function saveTruck(event) {
  event.preventDefault();
  clearBanner();
  if (!form.reportValidity()) return;
  const plate = normalizedPlate(truckIdInput.value);
  const existing = trucksByPlate.get(plate);
  const payload = {
    plate_number: plate,
    capacity_kg: Number(capacityInput.value),
    status: apiStatus[statusSelect.value],
    driver_name: driverNameInput.value.trim() || null,
    current_location: locationInput.value.trim() || null,
    notes: notesInput.value.trim() || null,
  };
  const submit = form.querySelector("button[type='submit']");
  submit.disabled = true;
  try {
    const saved = await FreshLinkAPI.request(
      existing ? `/api/transporter/trucks/${existing.truck_id}` : "/api/transporter/trucks",
      { method: existing ? "PATCH" : "POST", body: JSON.stringify(payload) },
    );
    trucksByPlate.set(normalizedPlate(saved.plate_number), saved);
    setBanner(existing ? "Truck status updated." : "Truck added and status saved.", "success");
    await loadTrucks();
  } catch (error) {
    if (error.status === 401) window.location.assign(FreshLinkAPI.loginUrl);
    else setBanner(error.message || "Unable to save this truck.", "error");
  } finally {
    submit.disabled = false;
  }
}

[truckIdInput, capacityInput, statusSelect, locationInput].forEach((element) => {
  element.addEventListener("input", updatePreview);
  element.addEventListener("change", updatePreview);
});
truckIdInput.addEventListener("change", fillExistingTruck);
form.addEventListener("submit", saveTruck);
document.getElementById("addAnotherTruckBtn").addEventListener("click", () => {
  form.reset();
  updatePreview();
  clearBanner();
  truckIdInput.focus();
  form.scrollIntoView({ behavior: "smooth", block: "start" });
});

loadTrucks();
