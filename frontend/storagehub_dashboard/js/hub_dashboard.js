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

document.querySelectorAll('.confirm-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    const row = document.querySelector('tr[data-row-id="' + btn.dataset.rowId + '"]');
    const pill = row.querySelector('.status-pill');
    pill.textContent = 'Confirmed';
    pill.classList.remove('limited');
    pill.classList.add('available');
    btn.replaceWith(document.createTextNode('—'));
    // TODO: replace with actual POST to backend allocation-confirmation endpoint
    // fetch(`/api/hub/allocations/${btn.dataset.rowId}/confirm`, { method: 'POST' })
  });
});
