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
