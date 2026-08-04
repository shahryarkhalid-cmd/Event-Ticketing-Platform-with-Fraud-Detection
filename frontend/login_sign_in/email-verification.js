/* =========================================================
   Tixora Email Verification Page — Script
   ---------------------------------------------------------
   Flow: Sign Up -> (this page) -> Log In -> Role Selection

   BACKEND CONTRACT (confirmed against the actual FastAPI source):

     POST /auth/verify-email          { email, code }     — PUBLIC, no auth header
       -> 200 { detail: "Email verified successfully. You can now log in." }
       -> 400 { detail: "Incorrect verification code" | "Code expired or not found..." }

     POST /auth/resend-verification   { email }           — PUBLIC, no auth header
       -> 200 { detail: "Verification code sent to your email" }
       -> 404 { detail: "No account found with this email" }
       -> 400 { detail: "This account is already verified" }

   The OTP is already sent automatically as part of POST /auth/register
   (see services/Verification_service.py's generate_and_send_otp, called from
   inside register_user), so this page does NOT need to trigger a "send code"
   call on load — only "Resend Code" calls the backend again.

   Verifying does NOT return an access token (see verify_otp in
   Verification_service.py) — the account still has to log in for real
   afterwards, so on success this redirects to login.html rather than
   straight to Role Selection.
   ========================================================= */
(function () {
  'use strict';

  var API_BASE = 'http://localhost:8000';
  var RESEND_COOLDOWN_S = 60;

  var pendingEmail = sessionStorage.getItem('pending_verification_email');
  if (!pendingEmail) {
    // Nobody should land here without having just signed up.
    window.location.href = 'signup.html';
    return;
  }

  var form = document.getElementById('verify-form');
  var otpInputs = Array.prototype.slice.call(document.querySelectorAll('.otp-digit'));
  var otpError = document.getElementById('otp-error');
  var submitBtn = document.getElementById('submit-btn');
  var formStatus = document.getElementById('form-status');
  var resendLink = document.getElementById('resend-link');
  var resendTimerEl = document.getElementById('resend-timer');
  var emailTargetEl = document.getElementById('verify-email-target');

  emailTargetEl.textContent = pendingEmail;

  function formatErrorDetail(detail) {
    if (!detail) return '';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(function (d) {
        if (typeof d === 'string') return d;
        var field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : '';
        return field ? (field + ': ' + d.msg) : (d.msg || JSON.stringify(d));
      }).join('; ');
    }
    return detail.msg || JSON.stringify(detail);
  }

  function showStatus(message, isError) {
    formStatus.textContent = message;
    formStatus.classList.toggle('is-error', Boolean(isError));
  }

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.classList.toggle('is-loading', isLoading);
  }

  /* ---------------------------------------------------
     OTP box behavior: auto-advance, backspace, paste-split
     --------------------------------------------------- */
  otpInputs.forEach(function (input, index) {
    input.addEventListener('input', function () {
      input.value = input.value.replace(/[^0-9]/g, '').slice(0, 1);
      input.classList.toggle('is-filled', Boolean(input.value));
      input.classList.remove('is-invalid');
      if (input.value && index < otpInputs.length - 1) {
        otpInputs[index + 1].focus();
      }
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace' && !input.value && index > 0) {
        otpInputs[index - 1].focus();
      }
    });

    input.addEventListener('paste', function (e) {
      var pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/[^0-9]/g, '');
      if (!pasted) return;
      e.preventDefault();
      pasted.slice(0, otpInputs.length).split('').forEach(function (digit, i) {
        if (otpInputs[i]) {
          otpInputs[i].value = digit;
          otpInputs[i].classList.add('is-filled');
        }
      });
      var next = otpInputs[Math.min(pasted.length, otpInputs.length - 1)];
      if (next) next.focus();
    });
  });

  function getCode() {
    return otpInputs.map(function (i) { return i.value; }).join('');
  }

  function markInvalid() {
    otpInputs.forEach(function (i) { i.classList.add('is-invalid'); });
  }

  function clearInvalid() {
    otpInputs.forEach(function (i) { i.classList.remove('is-invalid'); });
  }

  /* ---------------------------------------------------
     API calls
     --------------------------------------------------- */
  function resendVerification(email) {
    return fetch(API_BASE + '/auth/resend-verification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email })
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, message: formatErrorDetail(data.detail) };
      });
    }).catch(function (err) {
      console.error('resend-verification failed:', err);
      return { ok: false, message: 'Network error. Please try again.' };
    });
  }

  function verifyCode(email, code) {
    return fetch(API_BASE + '/auth/verify-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, code: code })
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) {
          console.error('POST /auth/verify-email → ' + res.status + ': ' + formatErrorDetail(data.detail));
          return { ok: false, message: formatErrorDetail(data.detail) };
        }
        return { ok: true };
      });
    }).catch(function (err) {
      console.error('verify-email failed:', err);
      return { ok: false, message: 'Network error. Please try again.' };
    });
  }

  /* ---------------------------------------------------
     Resend cooldown
     --------------------------------------------------- */
  var cooldownTimer = null;

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
    resendVerification(pendingEmail).then(function (result) {
      showStatus(result.ok ? 'A new code has been sent to your email.' : (result.message || 'Couldn\u2019t resend the code — please try again shortly.'), !result.ok);
      startResendCooldown();
    });
  });

  /* ---------------------------------------------------
     Submit
     --------------------------------------------------- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var code = getCode();

    if (code.length !== 6) {
      markInvalid();
      otpError.textContent = 'Please enter all 6 digits.';
      otpInputs[0].focus();
      return;
    }
    clearInvalid();
    otpError.textContent = '';
    showStatus('', false);
    setLoading(true);

    verifyCode(pendingEmail, code)
      .then(function (result) {
        if (result.ok) {
          showStatus('Email verified — redirecting you to log in…', false);
          sessionStorage.removeItem('pending_verification_email');
          // verify-email doesn't return an access token, so the user logs in
          // for real next — login.js then sends them to Role Selection
          // (first time) or straight to their dashboard (returning users).
          sessionStorage.setItem('just_verified_email', pendingEmail);
          window.location.href = 'login.html';
        } else {
          markInvalid();
          otpError.textContent = result.message || 'That code isn\u2019t right. Please try again.';
          setLoading(false);
        }
      });
  });

  startResendCooldown();
  otpInputs[0].focus();


  /* ---------------------------------------------------
     "Code sent" popup — shown once on page load
     --------------------------------------------------- */
  function showEmailSentPopup() {
    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);display:flex;align-items:center;justify-content:center;z-index:9999;font-family:\'Inter\',sans-serif;';
    overlay.innerHTML =
      '<div style="background:#fff;border-radius:16px;padding:28px 24px;max-width:340px;width:90%;text-align:center;box-shadow:0 20px 50px rgba(0,0,0,0.3);">' +
        '<p style="margin:0 0 8px;font-weight:600;color:#001F54;font-size:16px;">Check your email</p>' +
        '<p style="margin:0 0 20px;color:#555;font-size:14px;">We\u2019ve sent a code to <strong>' + pendingEmail + '</strong>. Don\u2019t see it? Check your spam or junk folder.</p>' +
        '<button id="email-sent-ok" style="width:100%;padding:10px;border-radius:999px;border:none;background:#001F54;color:#fff;cursor:pointer;">Got it</button>' +
      '</div>';
    document.body.appendChild(overlay);
    document.getElementById('email-sent-ok').addEventListener('click', function () {
      overlay.remove();
    });
  }

  showEmailSentPopup();

})();

