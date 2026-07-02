// I made the greeting change with the time of day so the workspace feels
// a little more alive than a static "Good Morning" that's wrong by noon.

document.addEventListener('DOMContentLoaded', function () {
  var greetingEl = document.querySelector('.js-greeting');

  if (!greetingEl) {
    return;
  }

  var hour = new Date().getHours();
  var greeting = 'Good Morning';

  if (hour >= 12 && hour < 17) {
    greeting = 'Good Afternoon';
  } else if (hour >= 17) {
    greeting = 'Good Evening';
  }

  greetingEl.textContent = greeting + ', Admin.';
});
