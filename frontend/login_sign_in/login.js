/* =========================================================
   Tixora Login Page — Script
   ========================================================= */
(function () {
  'use strict';

  const form = document.getElementById('login-form');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const emailError = document.getElementById('email-error');
  const passwordError = document.getElementById('password-error');
  const passwordToggle = document.getElementById('password-toggle');
  const submitBtn = document.getElementById('submit-btn');
  const formStatus = document.getElementById('form-status');
  const googleBtn = document.getElementById('google-btn');
  const appleBtn = document.getElementById('apple-btn');

  const MIN_PASSWORD_LENGTH = 8;

  // Same formatting as signup.js — FastAPI's 422 "detail" is often an
  // array of {loc, msg, type} objects, not a plain string.
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
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // If we just came from a successful Email Verification, greet the user
  // and pre-fill their email so they only have to type their password.
  (function showJustVerifiedMessage() {
    const justVerifiedEmail = sessionStorage.getItem('just_verified_email');
    if (!justVerifiedEmail) return;
    sessionStorage.removeItem('just_verified_email');
    emailInput.value = justVerifiedEmail;
    formStatus.textContent = 'Email verified! Please log in to continue.';
    formStatus.classList.remove('is-error');
  })();


  /* ---------------------------------------------------
     Password show / hide toggle
     --------------------------------------------------- */
  passwordToggle.addEventListener('click', function () {
    const willReveal = passwordInput.type === 'password';
    passwordInput.type = willReveal ? 'text' : 'password';

    passwordToggle.querySelector('.icon-eye').classList.toggle('is-active', !willReveal);
    passwordToggle.querySelector('.icon-eye-off').classList.toggle('is-active', willReveal);

    passwordToggle.setAttribute('aria-pressed', String(willReveal));
    passwordToggle.setAttribute('aria-label', willReveal ? 'Hide password' : 'Show password');
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

  function validateEmail(showEmptyError) {
    const value = emailInput.value.trim();

    if (!value) {
      if (showEmptyError) {
        setFieldState(emailInput, emailError, 'Email address is required.');
      } else {
        clearFieldState(emailInput, emailError);
      }
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
      if (showEmptyError) {
        setFieldState(passwordInput, passwordError, 'Password is required.');
      } else {
        clearFieldState(passwordInput, passwordError);
      }
      return false;
    }

    if (value.length < MIN_PASSWORD_LENGTH) {
      setFieldState(passwordInput, passwordError, `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return false;
    }

    setFieldState(passwordInput, passwordError, '');
    return true;
  }

  /* Live validation as the user types, without nagging before they've typed anything */
  emailInput.addEventListener('input', () => validateEmail(false));
  emailInput.addEventListener('blur', () => validateEmail(true));

  passwordInput.addEventListener('input', () => validatePassword(false));
  passwordInput.addEventListener('blur', () => validatePassword(true));

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
   * Placeholder login handler.
   * Replace the inside of this function with a real API call, e.g.:
   *
   *   const response = await fetch('/api/auth/login', {
   *     method: 'POST',
   *     headers: { 'Content-Type': 'application/json' },
   *     body: JSON.stringify({ email, password })
   *   });
   */
  async function handleLogin(email, password) {
  try {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      let detail = '';
      try { const errBody = await response.json(); detail = formatErrorDetail(errBody.detail); } catch (e) { /* ignore */ }
      console.error(`POST /auth/login → ${response.status}${detail ? `: ${detail}` : ''}`);
      return { ok: false };
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);

    // Find out whether this account already picked a role. First-time
    // users (role_selected === false) go to the role-selection page
    // exactly once; everyone else goes straight to their dashboard.
    const meResponse = await fetch('http://localhost:8000/users/me', {
      headers: { Authorization: `Bearer ${data.access_token}` }
    });

    if (!meResponse.ok) {
      console.error(`GET /users/me → ${meResponse.status}`);
      return { ok: false };
    }

    const me = await meResponse.json();
    return { ok: true, roleSelected: me.role_selected, role: me.role };
  } catch (err) {
    console.error('Login request failed:', err);
    return { ok: false };
  }
}
  form.addEventListener('submit', function (event) {
    event.preventDefault();

    const isEmailValid = validateEmail(true);
    const isPasswordValid = validatePassword(true);

    if (!isEmailValid || !isPasswordValid) {
      showStatus('Please fix the errors above and try again.', true);
      (isEmailValid ? passwordInput : emailInput).focus();
      return;
    }

    showStatus('', false);
    setLoading(true);

    handleLogin(emailInput.value.trim(), passwordInput.value)
      .then((result) => {
        if (result && result.ok) {
          // if (!result.roleSelected) {
          //   showStatus('Login successful — let\'s set up your account…', false);
          //   window.location.href = '../role/index.html';
          //   return;
          // }

          if (result.role === 'organizer') {
            showStatus('Login successful — redirecting to your dashboard…', false);
            window.location.href = '../dashboard/dashboard.html';
          } else {
            showStatus('Login successful — redirecting to events…', false);
            window.location.href = '../customer-window/index.html';
          }
        } else {
          showStatus('Incorrect email or password. Please try again.', true);
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
     Social login placeholders
     --------------------------------------------------- */
  function handleSocialLogin(provider) {
    showStatus(`Redirecting to ${provider} sign-in…`, false);
    // Hook up real OAuth redirect here, e.g. window.location.href = '/auth/google';
  }

  googleBtn?.addEventListener('click', () => handleSocialLogin('Google'));
  appleBtn?.addEventListener('click', () => handleSocialLogin('Apple'));

})();
