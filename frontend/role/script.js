/* =========================================================
   Tixora Role Selection Page — Script
   ========================================================= */
(function () {
  'use strict';

  var roleOptions = document.querySelectorAll('.role-option');

  roleOptions.forEach(function (button) {
    button.addEventListener('click', handleSelect);
    button.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleSelect(event);
      }
    });
  });

  function handleSelect(event) {
    var button = event.currentTarget;
    spawnRipple(button, event);

    var destination = button.getAttribute('data-destination');

    // Give the ripple / press animation a moment to play before navigating.
    window.setTimeout(function () {
      navigateTo(destination);
    }, 260);
  }

  function spawnRipple(button, event) {
    var host = button.querySelector('.role-option__cta');
    if (!host) return;

    var existing = host.querySelector('.ripple');
    if (existing) existing.remove();

    var rect = host.getBoundingClientRect();
    var size = Math.max(rect.width, rect.height);
    var ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = size + 'px';

    var originX, originY;
    if (event.clientX && event.clientY) {
      originX = event.clientX - rect.left - size / 2;
      originY = event.clientY - rect.top - size / 2;
    } else {
      originX = rect.width / 2 - size / 2;
      originY = rect.height / 2 - size / 2;
    }

    ripple.style.left = originX + 'px';
    ripple.style.top = originY + 'px';
    host.appendChild(ripple);

    ripple.addEventListener('animationend', function () {
      ripple.remove();
    });
  }

  /**
   * Placeholder navigation handler.
   * Update the data-destination attributes on each .role-option button
   * in index.html to point at the real Customer / Organizer login routes.
   */
  function navigateTo(destination) {
    if (!destination) return;
    window.location.href = destination;
  }

})();
