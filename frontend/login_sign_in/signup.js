/* =========================================================
   Tixora Sign Up Page — Script
   ========================================================= */
(function () {
  'use strict';

  const form = document.getElementById('signup-form');
  const fullnameInput = document.getElementById('fullname');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmInput = document.getElementById('confirm-password');
  const termsInput = document.getElementById('terms');

  const fullnameError = document.getElementById('fullname-error');
  const emailError = document.getElementById('email-error');
  const passwordError = document.getElementById('password-error');
  const confirmError = document.getElementById('confirm-password-error');
  const termsError = document.getElementById('terms-error');

  const submitBtn = document.getElementById('submit-btn');
  const formStatus = document.getElementById('form-status');
  const googleBtn = document.getElementById('google-btn');
  const appleBtn = document.getElementById('apple-btn');

  const MIN_PASSWORD_LENGTH = 8;
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // FastAPI's error "detail" for a 422 is usually an array of
  // {loc, msg, type} validation objects, not a plain string — this turns
  // that into readable text instead of it printing as [object Object].
  function formatErrorDetail(detail) {
    if (!detail) return '';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => {
        if (typeof d === 'string') return d;
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : '';
        return field ? `${field}: ${d.msg}` : (d.msg || JSON.stringify(d));
      }).join('; ');
    }
    if (typeof detail === 'object') return detail.msg || JSON.stringify(detail);
    return String(detail);
  }

  /* ---------------------------------------------------
     Password show / hide toggles (works for both fields)
     --------------------------------------------------- */
  document.querySelectorAll('.field__toggle').forEach(function (toggle) {
    const targetInput = document.getElementById(toggle.dataset.target);

    toggle.addEventListener('click', function () {
      const willReveal = targetInput.type === 'password';
      targetInput.type = willReveal ? 'text' : 'password';

      toggle.querySelector('.icon-eye').classList.toggle('is-active', !willReveal);
      toggle.querySelector('.icon-eye-off').classList.toggle('is-active', willReveal);

      toggle.setAttribute('aria-pressed', String(willReveal));
      toggle.setAttribute('aria-label', willReveal ? 'Hide password' : 'Show password');
    });
  });

  /* ---------------------------------------------------
     Field-level validation helpers
     --------------------------------------------------- */
  function setFieldState(input, errorEl, message) {
    if (message) {
      input.classList.remove('is-valid');
      input.classList.add('is-invalid');
      input.setAttribute('aria-invalid', 'true');
      errorEl.textContent = message;
      errorEl.classList.add('is-visible');
    } else {
      input.classList.remove('is-invalid');
      input.classList.add('is-valid');
      input.setAttribute('aria-invalid', 'false');
      errorEl.textContent = '';
      errorEl.classList.remove('is-visible');
    }
  }

  function clearFieldState(input, errorEl) {
    input.classList.remove('is-valid', 'is-invalid');
    input.setAttribute('aria-invalid', 'false');
    errorEl.textContent = '';
    errorEl.classList.remove('is-visible');
  }

  function validateFullname(showEmptyError) {
    const value = fullnameInput.value.trim();
    if (!value) {
      showEmptyError ? setFieldState(fullnameInput, fullnameError, 'Full name is required.') : clearFieldState(fullnameInput, fullnameError);
      return false;
    }
    if (value.length < 2) {
      setFieldState(fullnameInput, fullnameError, 'Please enter your full name.');
      return false;
    }
    setFieldState(fullnameInput, fullnameError, '');
    return true;
  }

  function validateEmail(showEmptyError) {
    const value = emailInput.value.trim();
    if (!value) {
      showEmptyError ? setFieldState(emailInput, emailError, 'Email address is required.') : clearFieldState(emailInput, emailError);
      return false;
    }
    if (!EMAIL_PATTERN.test(value)) {
      setFieldState(emailInput, emailError, 'Please enter a valid email address.');
      return false;
    }
    setFieldState(emailInput, emailError, '');
    return true;
  }

  function validatePassword(showEmptyError) {
    const value = passwordInput.value;
    if (!value) {
      showEmptyError ? setFieldState(passwordInput, passwordError, 'Password is required.') : clearFieldState(passwordInput, passwordError);
      return false;
    }
    if (value.length < MIN_PASSWORD_LENGTH) {
      setFieldState(passwordInput, passwordError, `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return false;
    }
    setFieldState(passwordInput, passwordError, '');
    return true;
  }

  function validateConfirm(showEmptyError) {
    const value = confirmInput.value;
    if (!value) {
      showEmptyError ? setFieldState(confirmInput, confirmError, 'Please confirm your password.') : clearFieldState(confirmInput, confirmError);
      return false;
    }
    if (value !== passwordInput.value) {
      setFieldState(confirmInput, confirmError, 'Passwords do not match.');
      return false;
    }
    setFieldState(confirmInput, confirmError, '');
    return true;
  }

  function validateTerms() {
    if (!termsInput.checked) {
      termsInput.classList.add('is-invalid');
      termsError.textContent = 'You must agree to the Terms of Service to continue.';
      termsError.classList.add('is-visible');
      return false;
    }
    termsInput.classList.remove('is-invalid');
    termsError.textContent = '';
    termsError.classList.remove('is-visible');
    return true;
  }

  fullnameInput.addEventListener('input', () => validateFullname(false));
  fullnameInput.addEventListener('blur', () => validateFullname(true));

  emailInput.addEventListener('input', () => validateEmail(false));
  emailInput.addEventListener('blur', () => validateEmail(true));

  passwordInput.addEventListener('input', () => {
    validatePassword(false);
    if (confirmInput.value) validateConfirm(true);
  });
  passwordInput.addEventListener('blur', () => validatePassword(true));

  confirmInput.addEventListener('input', () => validateConfirm(false));
  confirmInput.addEventListener('blur', () => validateConfirm(true));

  termsInput.addEventListener('change', validateTerms);

  /* ---------------------------------------------------
     Submit handling
     --------------------------------------------------- */
  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.classList.toggle('is-loading', isLoading);
  }

  function showStatus(message, isError) {
    formStatus.textContent = message;
    formStatus.classList.toggle('is-error', Boolean(isError));
  }

  /**
   * BACKEND CONTRACT (confirmed against the actual FastAPI source):
   *
   *   POST /auth/register   { full_name, email, password }   — no `role` field exists on
   *     this endpoint's schema (UserCreate has none), so nothing needs to be sent for it.
   *     Returns only { message } — NOT an access token. The backend automatically
   *     generates and emails a 6-digit OTP as part of registration
   *     (see services/Verification_service.py's generate_and_send_otp), so there's
   *     nothing to trigger separately here.
   *
   *   POST /auth/login      { email, password }
   *     Returns 403 "Please verify your email before logging in" for any account
   *     where is_verified is still false — i.e. a brand-new account CANNOT log in
   *     yet. So there is no "auto-login right after signup" possible; the user
   *     must verify their email first, then log in for real afterwards.
   */
  async function handleSignup(fullname, email, password) {
  try {
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: fullname,
        email: email,
        password: password
      })
    });

    if (!response.ok) {
      let detail = '';
      try { const errBody = await response.json(); detail = formatErrorDetail(errBody.detail); } catch (e) { /* ignore */ }
      console.error(`POST /auth/register → ${response.status}${detail ? `: ${detail}` : ''}`);
      return { ok: false, message: detail };
    }

    return { ok: true };
  } catch (err) {
    console.error('Signup request failed:', err);
    return { ok: false };
  }
}

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    const isNameValid = validateFullname(true);
    const isEmailValid = validateEmail(true);
    const isPasswordValid = validatePassword(true);
    const isConfirmValid = validateConfirm(true);
    const isTermsValid = validateTerms();

    if (!isNameValid || !isEmailValid || !isPasswordValid || !isConfirmValid || !isTermsValid) {
      showStatus('Please fix the errors above and try again.', true);
      return;
    }

    showStatus('', false);
    setLoading(true);

    handleSignup(fullnameInput.value.trim(), emailInput.value.trim(), passwordInput.value)
      .then((result) => {
        if (result && result.ok) {
          showStatus('Account created — let\'s verify your email…', false);
          // Required flow: Sign Up -> Email Verification -> Log In -> Role Selection.
          // email-verification.js reads this to show which address the code was sent to,
          // and to send it back along with the code when calling /auth/verify-email.
          sessionStorage.setItem('pending_verification_email', emailInput.value.trim());
          window.location.href = 'email-verification.html';
        } else {
          showStatus((result && result.message) || 'Something went wrong. Please try again.', true);
        }
      })
      .catch(() => {
        showStatus('Something went wrong. Please try again.', true);
      })
      .finally(() => {
        setLoading(false);
      });
  });

  /* ---------------------------------------------------
     Social sign-up placeholders
     --------------------------------------------------- */
  function handleSocialSignup(provider) {
    showStatus(`Redirecting to ${provider} sign-up…`, false);
    // Hook up real OAuth redirect here, e.g. window.location.href = '/auth/google';
  }

  googleBtn?.addEventListener('click', () => handleSocialSignup('Google'));
  appleBtn?.addEventListener('click', () => handleSocialSignup('Apple'));

})();
