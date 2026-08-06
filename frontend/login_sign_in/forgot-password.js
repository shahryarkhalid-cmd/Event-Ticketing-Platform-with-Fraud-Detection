/* =========================================================
   Tixora Forgot Password — Script
   ---------------------------------------------------------
   Single page, four animated steps, no page reloads:
     0: Enter Email  -> 1: Enter Code  -> 2: New Password -> 3: Success

   BACKEND CONTRACT (placeholder — confirm exact routes with the backend
   team; this frontend only assumes the following, unauthenticated):

     POST /auth/forgot-password        { email }
       -> 200 { ok: true }                (always 200 even if email unknown,
                                            to avoid leaking which emails exist)

     POST /auth/verify-reset-code      { email, code }
       -> 200 { reset_token: "..." }      short-lived token used for the next call
       -> 400/422 { detail: "..." }

     POST /auth/reset-password         { reset_token, new_password }
       -> 200 { ok: true }
       -> 400/422 { detail: "..." }
   ========================================================= */
(function () {
  'use strict';

  var API_BASE = 'https://event-ticketing-platform-with-fraud-detection-production.up.railway.app';
  var MIN_PASSWORD_LENGTH = 8;
  var EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var RESEND_COOLDOWN_S = 60;

  var state = { email: '', resetToken: '' };

  var formStatus = document.getElementById('fp-form-status');
  var progressDots = Array.prototype.slice.call(document.querySelectorAll('#fp-progress i'));
  var steps = Array.prototype.slice.call(document.querySelectorAll('.fp-step'));

  function formatErrorDetail(detail) {
    if (!detail) return '';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(function (d) { return (d && d.msg) ? d.msg : JSON.stringify(d); }).join('; ');
    }
    return detail.msg || JSON.stringify(detail);
  }

  function showStatus(message, isError) {
    formStatus.textContent = message || '';
    formStatus.classList.toggle('is-error', Boolean(isError));
  }

  function goToStep(index) {
    steps.forEach(function (step) {
      step.classList.toggle('is-active', Number(step.dataset.step) === index);
    });
    progressDots.forEach(function (dot) {
      var n = Number(dot.dataset.step);
      dot.classList.toggle('is-active', n === index);
      dot.classList.toggle('is-done', n < index);
    });
    showStatus('', false);
  }

  function setLoading(btn, isLoading) {
    btn.disabled = isLoading;
    btn.classList.toggle('is-loading', isLoading);
  }

  /* ---------------------------------------------------
     Step 0 — Email
     --------------------------------------------------- */
  var emailForm = document.getElementById('fp-step-email');
  var emailInput = document.getElementById('fp-email');
  var emailError = document.getElementById('fp-email-error');
  var sendBtn = document.getElementById('fp-send-btn');

  function sendResetCode(email) {
    return fetch(API_BASE + '/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email })
    }).then(function (res) { return res.ok; })
      .catch(function (err) { console.error('forgot-password failed:', err); return false; });
  }

  emailForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var email = emailInput.value.trim();
    if (!email || !EMAIL_PATTERN.test(email)) {
      emailError.textContent = 'Please enter a valid email address.';
      return;
    }
    emailError.textContent = '';
    setLoading(sendBtn, true);
    showStatus('Sending verification code…', false);

    sendResetCode(email).then(function (ok) {
      setLoading(sendBtn, false);
      state.email = email;
      document.getElementById('fp-email-target').textContent = email;
      if (!ok) console.warn('Could not reach /auth/forgot-password — confirm this endpoint exists on the backend.');

      // Show spam-folder notice; advance to the code step only after user taps OK
      var spamModal = document.getElementById('fp-spam-modal');
      spamModal.style.display = 'flex';
      document.getElementById('fp-spam-ok-btn').onclick = function () {
        spamModal.style.display = 'none';
        goToStep(1);
        startResendCooldown();
      };
    });
  });

  /* ---------------------------------------------------
     Step 1 — Code
     --------------------------------------------------- */
  var codeForm = document.getElementById('fp-step-code');
  var otpInputs = Array.prototype.slice.call(document.querySelectorAll('#fp-otp-row .otp-digit'));
  var codeError = document.getElementById('fp-code-error');
  var verifyBtn = document.getElementById('fp-verify-btn');
  var resendLink = document.getElementById('fp-resend-link');
  var resendTimerEl = document.getElementById('fp-resend-timer');
  var cooldownTimer = null;

  otpInputs.forEach(function (input, index) {
    input.addEventListener('input', function () {
      input.value = input.value.replace(/[^0-9]/g, '').slice(0, 1);
      input.classList.toggle('is-filled', Boolean(input.value));
      input.classList.remove('is-invalid');
      if (input.value && index < otpInputs.length - 1) otpInputs[index + 1].focus();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && !input.value && index > 0) otpInputs[index - 1].focus();
    });
    input.addEventListener('paste', function (e) {
      var pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/[^0-9]/g, '');
      if (!pasted) return;
      e.preventDefault();
      pasted.slice(0, otpInputs.length).split('').forEach(function (digit, i) {
        if (otpInputs[i]) { otpInputs[i].value = digit; otpInputs[i].classList.add('is-filled'); }
      });
    });
  });

  function getCode() {
    return otpInputs.map(function (i) { return i.value; }).join('');
  }

  function startResendCooldown() {
    var remaining = RESEND_COOLDOWN_S;
    resendLink.classList.add('is-disabled');
    resendLink.setAttribute('disabled', 'true');
    resendTimerEl.textContent = ' (' + remaining + 's)';
    clearInterval(cooldownTimer);
    cooldownTimer = setInterval(function () {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(cooldownTimer);
        resendLink.classList.remove('is-disabled');
        resendLink.removeAttribute('disabled');
        resendTimerEl.textContent = '';
      } else {
        resendTimerEl.textContent = ' (' + remaining + 's)';
      }
    }, 1000);
  }

  resendLink.addEventListener('click', function (e) {
    e.preventDefault();
    if (resendLink.classList.contains('is-disabled')) return;
    showStatus('Sending a new code…', false);
    sendResetCode(state.email).then(function (ok) {
      showStatus(ok ? 'A new code has been sent.' : 'Couldn\u2019t resend the code — please try again shortly.', !ok);
      startResendCooldown();
    });
  });

  function verifyResetCode(email, code) {
    return fetch(API_BASE + '/auth/verify-reset-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, code: code })
    }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          return { ok: false, message: formatErrorDetail(data.detail) };
        });
      }
      return res.json().then(function (data) { return { ok: true, resetToken: data.reset_token }; });
    }).catch(function (err) {
      console.error('verify-reset-code failed:', err);
      return { ok: false, message: 'Network error. Please try again.' };
    });
  }

  codeForm.addEventListener('submit', function (e) {
  e.preventDefault();
  var code = getCode();
  if (code.length !== 6) {
    codeError.textContent = 'Please enter all 6 digits.';
    return;
  }
  codeError.textContent = '';
  showStatus('', false);
  setLoading(verifyBtn, true);
  showStatus('Verifying code…', false);

  verifyResetCode(state.email, code).then(function (result) {
    setLoading(verifyBtn, false);
    if (result.ok) {
      state.resetToken = result.resetToken || '';
      clearInterval(cooldownTimer);
      goToStep(2);
    } else {
      showStatus('', false);
      otpInputs.forEach(function (i) { i.classList.add('is-invalid'); });
      codeError.textContent = result.message || 'That code isn\u2019t right. Please try again.';
    }
  });
});

  /* ---------------------------------------------------
     Step 2 — New password
     --------------------------------------------------- */
  var passwordForm = document.getElementById('fp-step-password');
  var newPasswordInput = document.getElementById('fp-new-password');
  var confirmPasswordInput = document.getElementById('fp-confirm-password');
  var newPasswordError = document.getElementById('fp-new-password-error');
  var confirmPasswordError = document.getElementById('fp-confirm-password-error');
  var resetBtn = document.getElementById('fp-reset-btn');

  function resetPassword(resetToken, newPassword) {
    return fetch(API_BASE + '/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reset_token: resetToken, new_password: newPassword })
    }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          return { ok: false, message: formatErrorDetail(data.detail) };
        });
      }
      return { ok: true };
    }).catch(function (err) {
      console.error('reset-password failed:', err);
      return { ok: false, message: 'Network error. Please try again.' };
    });
  }

  passwordForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var pw = newPasswordInput.value;
    var confirm = confirmPasswordInput.value;
    var valid = true;

    if (!pw || pw.length < MIN_PASSWORD_LENGTH) {
      newPasswordError.textContent = 'Password must be at least ' + MIN_PASSWORD_LENGTH + ' characters.';
      valid = false;
    } else {
      newPasswordError.textContent = '';
    }

    if (!confirm || confirm !== pw) {
      confirmPasswordError.textContent = 'Passwords do not match.';
      valid = false;
    } else {
      confirmPasswordError.textContent = '';
    }

    if (!valid) return;

    setLoading(resetBtn, true);
    showStatus('Updating your password…', false);

    resetPassword(state.resetToken, pw).then(function (result) {
      setLoading(resetBtn, false);
      if (result.ok) {
        goToStep(3);
      } else {
        showStatus(result.message || 'Couldn\u2019t update your password. Please try again.', true);
      }
    });
  });

  goToStep(0);

})();
