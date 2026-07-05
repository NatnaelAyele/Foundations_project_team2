// Mobile menu toggle (inlined so it works without an external file).
document.addEventListener('click', function (e) {
  var toggle = document.querySelector('.menu-toggle');
  var navLinks = document.querySelector('.nav-links');
  if (!toggle || !navLinks) return;
  if (toggle.contains(e.target)) {
    var isOpen = navLinks.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  } else if (e.target.closest('.nav-links a')) {
    navLinks.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }
});

const truckIdInput = document.getElementById('truckId');
const capacityInput = document.getElementById('capacity');
const statusSelect = document.getElementById('status');
const locationInput = document.getElementById('location');
const previewTruck = document.getElementById('previewTruck');
const previewCapacity = document.getElementById('previewCapacity');
const previewStatus = document.getElementById('previewStatus');
const previewLocation = document.getElementById('previewLocation');
const form = document.getElementById('truckStatusForm');
const confirmBanner = document.getElementById('confirmBanner');
const STATUS_LABELS = {
  available: 'Available',
  'en-route': 'En route',
  full: 'Full',
  maintenance: 'Maintenance',
};
const STATUS_CLASSES = {
  available: 'available',
  'en-route': 'en-route',
  full: 'full',
  maintenance: 'maintenance',
};
function updatePreview() {
  previewTruck.textContent = truckIdInput.value || '—';
  previewCapacity.textContent = capacityInput.value ? `${Number(capacityInput.value).toLocaleString()} kg` : '—';
  previewLocation.textContent = locationInput.value || '—';
  const status = statusSelect.value;
  previewStatus.className = 'status-pill ' + (STATUS_CLASSES[status] || 'limited');
  previewStatus.textContent = STATUS_LABELS[status] || 'Not set';
}
[truckIdInput, capacityInput, statusSelect, locationInput].forEach((el) => {
  el.addEventListener('input', updatePreview);
  el.addEventListener('change', updatePreview);
});
form.addEventListener('submit', function (e) {
  e.preventDefault();
  // TODO: replace with actual POST to backend truck-status endpoint
  // fetch('/api/transporter/truck-status', { method: 'POST', body: new FormData(form) })
  confirmBanner.classList.add('visible');
  setTimeout(() => confirmBanner.classList.remove('visible'), 4000);
});
document.getElementById('addAnotherTruckBtn').addEventListener('click', function () {
  form.reset();
  updatePreview();
  confirmBanner.classList.remove('visible');
  form.querySelector('input, select, textarea').focus();
  form.scrollIntoView({ behavior: 'smooth', block: 'start' });
});
