/* =========================================================
   Tixora Payment Result Page — Script
   ---------------------------------------------------------
   One page, two outcomes, chosen by the URL:

     payment-result.html?status=success&order_id=15
     payment-result.html?status=cancel&order_id=15

   Stripe's checkout session should be created with those two
   URLs as success_url / cancel_url respectively (see
   Payment_services.py / create_checkout_session).

   If ?status= is missing but an order_id is present, the page
   defaults to the success flow — it polls the order and shows
   whatever the backend actually reports.

   The success flow polls GET /orders/{order_id} (authenticated)
   every POLL_INTERVAL_MS until status becomes "paid", or until
   POLL_TIMEOUT_MS elapses. Payment is only ever confirmed from
   that backend response, itself only updated by the existing
   Stripe webhook — never marked successful client-side.
   ========================================================= */
(function () {
  'use strict';

  // ---------------------------------------------------------
  // Config — adjust API_BASE if the backend isn't on localhost.
  // ---------------------------------------------------------
  const API_BASE = 'http://localhost:8000';
  const POLL_INTERVAL_MS = 2500;
  const POLL_TIMEOUT_MS = 60000; // stop polling after 60s and show the timeout state
  const DASHBOARD_URL = '../customer-window/index.html';

  const verifyState = document.getElementById('verify-state');
  const verifySubtitle = document.getElementById('verify-subtitle');
  const successState = document.getElementById('success-state');
  const cancelState = document.getElementById('cancel-state');
  const timeoutState = document.getElementById('timeout-state');
  const errorState = document.getElementById('error-state');
  const errorMessage = document.getElementById('error-message');
  const successIcon = document.getElementById('success-icon');
  const refreshBtn = document.getElementById('refresh-btn');
  const downloadLink = document.getElementById('download-ticket-link');

  const cancelOrderDetailList = document.getElementById('cancel-order-detail-list');
  const cancelOrderIdEl = document.getElementById('cancel-detail-order-id');
  const tryAgainBtn = document.getElementById('try-again-btn');

  const ALL_SECTIONS = [verifyState, successState, cancelState, timeoutState, errorState];

  function showOnly(el) {
    ALL_SECTIONS.forEach((section) => {
      section.classList.toggle('hidden', section !== el);
    });
  }

  function getParams() {
    return new URLSearchParams(window.location.search);
  }

  function getOrderId() {
    return getParams().get('order_id');
  }

  function getStatusParam() {
    const status = (getParams().get('status') || '').toLowerCase();
    return status; // 'success' | 'cancel' | 'cancelled' | ''
  }

  function getToken() {
    return localStorage.getItem('access_token');
  }

  function authHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  function money(value) {
    if (value === null || value === undefined || value === '') return '—';
    const num = Number(value);
    if (Number.isNaN(num)) return String(value);
    return num.toLocaleString(undefined, { style: 'currency', currency: 'USD' });
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit'
    });
  }

  /**
   * The exact shape of OrderRead isn't known from this page alone, so this
   * reads a handful of plausible field names defensively. If your OrderRead
   * schema uses different keys, adjust the paths below.
   */
  function readOrderFields(order) {
    const event = order.event || order.event_detail || {};
    return {
      orderId: order.id ?? order.order_id ?? '—',
      status: (order.status || order.payment_status || '').toLowerCase(),
      amount: order.total_amount ?? order.amount ?? order.total_price ?? order.total ?? null,
      eventName: event.title || event.name || order.event_name || '—',
      quantity: order.quantity ?? order.ticket_quantity ?? order.total_quantity ?? '—',
      purchaseDate: order.created_at ?? order.purchase_date ?? order.updated_at ?? null
    };
  }

  /* ---------------------------------------------------------
     Success flow
     --------------------------------------------------------- */
  function populateSuccess(order) {
    const fields = readOrderFields(order);
    document.getElementById('detail-order-id').textContent = `#${fields.orderId}`;
    document.getElementById('detail-amount').textContent = money(fields.amount);
    document.getElementById('detail-event').textContent = fields.eventName;
    document.getElementById('detail-quantity').textContent = fields.quantity;
    document.getElementById('detail-date').textContent = formatDate(fields.purchaseDate);

    showOnly(successState);

    // Play the check-draw / glow animation once.
    requestAnimationFrame(() => successIcon.classList.add('is-animating'));
  }

  async function fetchOrder(orderId) {
    const res = await fetch(`${API_BASE}/orders/${orderId}`, {
      headers: authHeaders()
    });
    if (res.status === 401 || res.status === 403) {
      throw new Error('AUTH');
    }
    if (!res.ok) {
      throw new Error('FETCH');
    }
    return res.json();
  }

  function pollUntilPaid(orderId) {
    const startedAt = Date.now();

    async function tick() {
      let order;
      try {
        order = await fetchOrder(orderId);
      } catch (err) {
        if (err.message === 'AUTH') {
          window.location.href = '../login_sign_in/login.html';
          return;
        }
        errorMessage.textContent = 'Unable to load your payment details. Please visit My Orders.';
        showOnly(errorState);
        return;
      }

      const fields = readOrderFields(order);

      if (fields.status === 'paid') {
        populateSuccess(order);
        return;
      }

      if (Date.now() - startedAt >= POLL_TIMEOUT_MS) {
        showOnly(timeoutState);
        return;
      }

      verifySubtitle.textContent = 'Hang tight while we confirm this with Stripe. This usually takes just a few seconds.';
      setTimeout(tick, POLL_INTERVAL_MS);
    }

    tick();
  }

  function runSuccessFlow(orderId) {
    if (!getToken()) {
      window.location.href = '../login_sign_in/login.html';
      return;
    }
    showOnly(verifyState);
    pollUntilPaid(orderId);
  }

  /* ---------------------------------------------------------
     Cancel flow
     --------------------------------------------------------- */
  function setTryAgainLoading(isLoading) {
    tryAgainBtn.disabled = isLoading;
    tryAgainBtn.textContent = isLoading ? 'Starting checkout…' : 'Try Again';
  }

  async function retryCheckout(orderId) {
    setTryAgainLoading(true);
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/checkout`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Could not start checkout');
      }

      // Redirect the whole page to Stripe's hosted checkout, same as the
      // original checkout flow in customer-window/script.js.
      window.location.href = data.checkout_url;
    } catch (err) {
      setTryAgainLoading(false);
      window.location.href = DASHBOARD_URL;
    }
  }

  function runCancelFlow(orderId) {
    if (orderId) {
      cancelOrderIdEl.textContent = `#${orderId}`;
      cancelOrderDetailList.classList.remove('hidden');
    }

    tryAgainBtn.addEventListener('click', () => {
      // No order to retry, or no active session — send the user back to
      // their dashboard rather than to the login page.
      if (!orderId || !getToken()) {
        window.location.href = DASHBOARD_URL;
        return;
      }
      retryCheckout(orderId);
    });

    showOnly(cancelState);
  }

  /* ---------------------------------------------------------
     Entry point
     --------------------------------------------------------- */
  function init() {
    const orderId = getOrderId();
    const status = getStatusParam();
    const isCancel = status === 'cancel' || status === 'cancelled';

    if (isCancel) {
      runCancelFlow(orderId);
      return;
    }

    if (!orderId) {
      errorMessage.textContent = 'No order was specified. Please visit My Orders.';
      showOnly(errorState);
      return;
    }

    runSuccessFlow(orderId);
  }

  refreshBtn.addEventListener('click', () => window.location.reload());

  // "Download Ticket" is a placeholder only, per spec — no handler wired yet.
  downloadLink.addEventListener('click', (event) => event.preventDefault());

  document.addEventListener('DOMContentLoaded', init);
})();
