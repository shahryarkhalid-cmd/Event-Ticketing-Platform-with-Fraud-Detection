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
   * Placeholder signup handler.
   * Replace the inside of this function with a real API call, e.g.:
   *
   *   const response = await fetch('/api/auth/signup', {
   *     method: 'POST',
   *     headers: { 'Content-Type': 'application/json' },
   *     body: JSON.stringify({ fullname, email, password })
   *   });
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
      return { ok: false };
    }

    // Immediately log the freshly-created account in so we have a token
    // to call /auth/select-role with on the role-selection page. The user
    // never sees a separate login step right after signing up.
    const loginResponse = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password })
    });

    if (!loginResponse.ok) {
      // Account was created but auto-login failed for some reason -
      // fall back to sending them to the login page.
      return { ok: true, autoLoggedIn: false };
    }

    const loginData = await loginResponse.json();
    localStorage.setItem('access_token', loginData.access_token);
    return { ok: true, autoLoggedIn: true };
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
        if (result && result.ok && result.autoLoggedIn) {
          showStatus('Account created — let\'s set up your account…', false);
          window.location.href = '../role/index.html';
        } else if (result && result.ok) {
          showStatus('Account created — redirecting you to log in…', false);
          window.location.href = 'login.html';
        } else {
          showStatus('Something went wrong. Please try again.', true);
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
