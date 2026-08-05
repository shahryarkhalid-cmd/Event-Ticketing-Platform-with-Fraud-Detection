/* =========================================================
   Tixora Role Selection Page — Script
   Calls POST /auth/select-role (one-time, backend-enforced) and then
   routes the user to the correct dashboard.
   ========================================================= */
(function () {
  'use strict';

  var API_BASE = 'https://event-ticketing-platform-with-fraud-detection-production.up.railway.app';

  var roleOptions = document.querySelectorAll('.role-option');
  var page = document.querySelector('.page');

  var token = localStorage.getItem('access_token');
  if (!token) {
    // No one should land on this page without being logged in first.
    window.location.href = '../login_sign_in/login.html';
    return;
  }

  // If this account already picked a role (e.g. someone bookmarked this
  // page, or hit back after already choosing), don't let them choose
  // again — just send them straight to their dashboard.
  checkExistingRole();

  function checkExistingRole() {
    fetch(API_BASE + '/users/me', {
      headers: { Authorization: 'Bearer ' + token }
    })
      .then(function (res) {
        if (!res.ok) throw new Error('me failed');
        return res.json();
      })
      .then(function (me) {
        if (me.role_selected) {
          redirectForRole(me.role);
        }
      })
      .catch(function () {
        // If we can't verify (e.g. token expired), send them back to log in.
        localStorage.removeItem('access_token');
        window.location.href = '../login_sign_in/login.html';
      });
  }

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
    var role = button.getAttribute('data-role');

    spawnRipple(button, event);
    setBusy(true);

    selectRole(role)
      .then(function (result) {
        if (result.ok) {
          window.setTimeout(function () {
            redirectForRole(role);
          }, 260);
        } else {
          setBusy(false);
          alert(result.message || 'Something went wrong. Please try again.');
        }
      });
  }

  function selectRole(role) {
    return fetch(API_BASE + '/auth/select-role', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + token
      },
      body: JSON.stringify({ role: role })
    })
      .then(function (res) {
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (data) {
            return { ok: false, message: data.detail };
          });
        }
        return { ok: true };
      })
      .catch(function (err) {
        console.error('Role selection request failed:', err);
        return { ok: false, message: 'Network error. Please try again.' };
      });
  }

  function redirectForRole(role) {
    if (role === 'organizer') {
      window.location.href = '../dashboard/dashboard.html';
    } else {
      window.location.href = '../customer-window/index.html';
    }
  }

  function setBusy(isBusy) {
    roleOptions.forEach(function (button) {
      button.disabled = isBusy;
    });
    if (page) page.style.opacity = isBusy ? '0.6' : '1';
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

})();
