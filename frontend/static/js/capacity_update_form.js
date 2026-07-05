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

const totalInput = document.getElementById('totalCapacity');
const availInput = document.getElementById('availableCapacity');
const capCurrent = document.getElementById('capCurrent');
const capTotalLabel = document.getElementById('capTotalLabel');
const capBarFill = document.getElementById('capBarFill');
const capStatus = document.getElementById('capStatus');
const form = document.getElementById('capacityForm');
const confirmBanner = document.getElementById('confirmBanner');
function updateCapacityVisual() {
  const total = parseFloat(totalInput.value) || 0;
  const available = parseFloat(availInput.value) || 0;
  capCurrent.textContent = available.toLocaleString();
  capTotalLabel.textContent = `/ ${total.toLocaleString()} kg total`;
  if (total === 0) {
    capBarFill.style.width = '0%';
    capBarFill.classList.remove('over-limit');
    capStatus.textContent = "Enter your hub's numbers to preview.";
    capStatus.classList.remove('warn');
    return;
  }
  const pct = Math.min((available / total) * 100, 100);
  capBarFill.style.width = pct + '%';
  if (available > total) {
    capBarFill.classList.add('over-limit');
    capStatus.textContent = "Available can't exceed total capacity — check your numbers.";
    capStatus.classList.add('warn');
  } else {
    capBarFill.classList.remove('over-limit');
    capStatus.classList.remove('warn');
    if (pct < 15) {
      capStatus.textContent = 'Nearly full — transporters will see limited space.';
    } else {
      capStatus.textContent = `${Math.round(pct)}% of capacity free for incoming produce.`;
    }
  }
}
totalInput.addEventListener('input', updateCapacityVisual);
availInput.addEventListener('input', updateCapacityVisual);
form.addEventListener('submit', function (e) {
  e.preventDefault();
  const available = parseFloat(availInput.value) || 0;
  const total = parseFloat(totalInput.value) || 0;
  if (available > total) {
    capStatus.textContent = "Fix available capacity before saving — it can't exceed total.";
    capStatus.classList.add('warn');
    return;
  }

  confirmBanner.classList.add('visible');
  setTimeout(() => confirmBanner.classList.remove('visible'), 4000);
});
