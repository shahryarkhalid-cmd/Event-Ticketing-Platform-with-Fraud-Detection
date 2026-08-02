/* =========================================================
   Tixora — Reusable Terms & Conditions Modal (shared component)
   ---------------------------------------------------------
   Usage: include shared/terms-modal.css + shared/terms-modal.js
   on any page, then mark a link/button with:

     <a href="#" class="js-terms-link" data-terms-checkbox="terms">
       Terms & Conditions
     </a>

   `data-terms-checkbox` is the id of the checkbox this trigger should
   auto-check when the user clicks "Confirm" inside the modal. If the
   attribute is omitted, the component falls back to the nearest
   checkbox input inside the same <form> (or the whole document as a
   last resort), so existing markup mostly works unmodified.

   The modal is injected once, lazily, on first use — pages that never
   open it pay zero extra DOM cost.
   ========================================================= */
(function (window, document) {
  'use strict';

  var overlayEl = null;
  var lastTrigger = null;

  var TERMS_SECTIONS = [
    {
      title: '1. Acceptance of Terms',
      body: 'By creating an account or publishing an event on Tixora, you agree to be bound by these Terms & Conditions and our Privacy Policy. If you do not agree, please do not use the platform.'
    },
    {
      title: '2. Account Responsibilities',
      body: 'You are responsible for maintaining the confidentiality of your account credentials and for all activity that occurs under your account, whether as a Customer or an Organizer.'
    },
    {
      title: '3. Event Listings & Ticketing',
      body: 'Organizers are solely responsible for the accuracy of their event listings, pricing, and availability. Tixora facilitates ticket sales and payment processing but is not the seller of record for any event.'
    },
    {
      title: '4. Payments & Refunds',
      body: 'All payments are processed through our payment partner. Refunds are governed by each event\u2019s stated refund policy, where provided, or Tixora\u2019s default policy otherwise.'
    },
    {
      title: '5. Prohibited Conduct',
      body: 'You may not use Tixora to list fraudulent events, resell tickets in violation of local law, or attempt to circumvent platform fees.'
    },
    {
      title: '6. Changes to These Terms',
      body: 'Tixora may update these Terms from time to time. Continued use of the platform after changes take effect constitutes acceptance of the revised Terms.'
    }
  ];

  function buildModal() {
    var overlay = document.createElement('div');
    overlay.className = 'terms-modal-overlay';
    overlay.setAttribute('aria-hidden', 'true');

    var sectionsHTML = TERMS_SECTIONS.map(function (s) {
      return '<h3>' + s.title + '</h3><p>' + s.body + '</p>';
    }).join('');

    overlay.innerHTML =
      '<div class="terms-modal" role="dialog" aria-modal="true" aria-labelledby="terms-modal-title">' +
        '<div class="terms-modal__header">' +
          '<h2 id="terms-modal-title">Terms &amp; Conditions</h2>' +
          '<button type="button" class="terms-modal__close" aria-label="Close">' +
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
              '<path d="M6 6L18 18M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
            '</svg>' +
          '</button>' +
        '</div>' +
        '<div class="terms-modal__body">' + sectionsHTML + '</div>' +
        '<div class="terms-modal__footer">' +
          '<button type="button" class="terms-modal__btn terms-modal__btn--cancel">Close</button>' +
          '<button type="button" class="terms-modal__btn terms-modal__btn--confirm">Confirm</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });
    overlay.querySelector('.terms-modal__close').addEventListener('click', closeModal);
    overlay.querySelector('.terms-modal__btn--cancel').addEventListener('click', closeModal);
    overlay.querySelector('.terms-modal__btn--confirm').addEventListener('click', function () {
      checkAssociatedCheckbox();
      closeModal();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay.classList.contains('is-open')) closeModal();
    });

    return overlay;
  }

  function findCheckbox(trigger) {
    if (!trigger) return null;
    var explicitId = trigger.getAttribute('data-terms-checkbox');
    if (explicitId) {
      var el = document.getElementById(explicitId);
      if (el) return el;
    }
    var form = trigger.closest('form');
    var scope = form || document;
    return (
      scope.querySelector('#terms') ||
      scope.querySelector('#f_terms') ||
      scope.querySelector('input[type="checkbox"][id*="terms" i]')
    );
  }

  function checkAssociatedCheckbox() {
    var checkbox = findCheckbox(lastTrigger);
    if (!checkbox || checkbox.checked) return;
    checkbox.checked = true;
    // Fire a real 'change' event so any existing validation/listeners
    // on the page (e.g. signup.js's validateTerms()) react normally.
    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function openModal(trigger) {
    lastTrigger = trigger || null;
    if (!overlayEl) overlayEl = buildModal();
    overlayEl.classList.add('is-open');
    overlayEl.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    if (!overlayEl) return;
    overlayEl.classList.remove('is-open');
    overlayEl.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  function bindTriggers(root) {
    var scope = root || document;
    scope.querySelectorAll('.js-terms-link').forEach(function (link) {
      if (link.dataset.termsBound) return;
      link.dataset.termsBound = '1';
      link.addEventListener('click', function (e) {
        e.preventDefault();
        openModal(link);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindTriggers(document);
  });

  // Exposed in case a page injects new Terms links dynamically
  // (e.g. after rendering a form), or wants to open the modal
  // programmatically without a trigger element.
  window.TixoraTermsModal = {
    open: openModal,
    close: closeModal,
    bind: bindTriggers
  };

})(window, document);
