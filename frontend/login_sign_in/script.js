/* ==========================================================================
   Tixora — Role Selection Page
   Handles ripple feedback, keyboard interaction, and role navigation.
   ========================================================================== */

(function () {
  "use strict";

  // Map each role to its destination login page.
  // Update these paths to match the real routes in production.
  var ROUTES = {
    customer: "customer-login.html",
    organizer: "organizer-login.html"
  };

  var roleButtons = document.querySelectorAll(".role-option");

  roleButtons.forEach(function (button) {
    button.addEventListener("click", handleSelect);
    button.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        handleSelect(event);
      }
    });
  });

  function handleSelect(event) {
    var button = event.currentTarget;
    spawnRipple(button, event);

    var role = button.getAttribute("data-role");
    var destination = ROUTES[role];

    // Give the ripple / press animation a moment to play before navigating.
    window.setTimeout(function () {
      navigateToRole(destination);
    }, 260);
  }

  function spawnRipple(button, event) {
    var rippleHost = button.querySelector(".role-button");
    if (!rippleHost) return;

    var existing = rippleHost.querySelector(".ripple");
    if (existing) existing.remove();

    var rect = rippleHost.getBoundingClientRect();
    var size = Math.max(rect.width, rect.height);
    var ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.width = ripple.style.height = size + "px";

    var originX, originY;
    if (event.clientX && event.clientY) {
      originX = event.clientX - rect.left - size / 2;
      originY = event.clientY - rect.top - size / 2;
    } else {
      originX = rect.width / 2 - size / 2;
      originY = rect.height / 2 - size / 2;
    }

    ripple.style.left = originX + "px";
    ripple.style.top = originY + "px";
    rippleHost.appendChild(ripple);

    ripple.addEventListener("animationend", function () {
      ripple.remove();
    });
  }

  function navigateToRole(destination) {
    if (!destination) return;
    window.location.href = destination;
  }
})();
