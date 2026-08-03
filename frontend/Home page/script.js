/* =========================================================
   TIXORA Landing Page — Script
   Sections: 1) Antigravity particle canvas engine
             2) Showcase tab switcher (updates URL bar + mockup)
             3) 3D perspective tilt on the browser-frame stage
             4) Mobile nav toggle
   ========================================================= */
(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* =======================================================
     1. ANTIGRAVITY PARTICLE CANVAS ENGINE
     ======================================================= */
  function initParticleCanvas() {
    const canvas = document.getElementById('antigravity-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const COLORS = ['#001F54', '#0B5ED7', '#4CC9F0'];
    const MOUSE_RADIUS = 150;
    const CLICK_RADIUS = 220;

    let particles = [];
    let mouse = { x: -9999, y: -9999 };
    let width, height, dpr;

    function resize() {
      dpr = window.devicePixelRatio || 1;
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = width + 'px';
      canvas.style.height = height + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seedParticles();
    }

    function seedParticles() {
      // Particle Density Equation: floor((W * H) / 6000)
      const count = Math.floor((width * height) / 6000);
      particles = new Array(count).fill(null).map(() => ({
        x: Math.random() * width,
        y: Math.random() * height,
        r: 1.0 + Math.random() * 2.5,          // 1.0px – 3.5px
        vx: (Math.random() - 0.5) * 0.8,        // -0.4 to +0.4
        vy: (Math.random() - 0.5) * 0.8,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        alpha: 0.25 + Math.random() * 0.5       // 0.25 – 0.75
      }));
    }

    function step() {
      ctx.clearRect(0, 0, width, height);

      for (const p of particles) {
        // Cursor repulsion forcefield
        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < MOUSE_RADIUS && d > 0.001) {
          const force = ((MOUSE_RADIUS - d) / MOUSE_RADIUS) * 5;
          p.vx += (dx / d) * force * 0.02;
          p.vy += (dy / d) * force * 0.02;
        }

        // Damping so click impulses / repulsion decay back to ambient drift
        p.vx *= 0.96;
        p.vy *= 0.96;

        p.x += p.vx;
        p.y += p.vy;

        // Wrap around edges instead of clamping, for a continuous field
        if (p.x < -10) p.x = width + 10;
        if (p.x > width + 10) p.x = -10;
        if (p.y < -10) p.y = height + 10;
        if (p.y > height + 10) p.y = -10;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = hexToRgba(p.color, p.alpha);
        ctx.fill();
      }

      requestAnimationFrame(step);
    }

    function hexToRgba(hex, alpha) {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    window.addEventListener('mousemove', (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });
    window.addEventListener('mouseleave', () => { mouse.x = -9999; mouse.y = -9999; });

    // Mouse-click shockwave burst
    window.addEventListener('click', (e) => {
      for (const p of particles) {
        const dx = p.x - e.clientX;
        const dy = p.y - e.clientY;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < CLICK_RADIUS && d > 0.001) {
          p.vx += -(dx / d) * 12 * 0.15;
          p.vy += -(dy / d) * 12 * 0.15;
        }
      }
    });

    window.addEventListener('resize', resize);
    resize();

    if (!prefersReducedMotion) {
      requestAnimationFrame(step);
    } else {
      // Draw a single static frame instead of a continuous loop
      step_static();
    }

    function step_static() {
      ctx.clearRect(0, 0, width, height);
      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = hexToRgba(p.color, p.alpha);
        ctx.fill();
      }
    }
  }

  /* =======================================================
     2. SHOWCASE TAB SWITCHER
     ======================================================= */
  function initShowcaseTabs() {
    const tabs = document.querySelectorAll('.showcase__tab');
    const mockups = document.querySelectorAll('.mockup');
    const urlBar = document.getElementById('browser-url');

    const URLS = {
      customer: 'https://tixora.app/events/live-discovery',
      organizer: 'https://tixora.app/organizer/dashboard'
    };

    function setActiveView(view) {
      tabs.forEach((tab) => {
        const isActive = tab.dataset.view === view;
        tab.classList.toggle('is-active', isActive);
        tab.setAttribute('aria-selected', String(isActive));
      });
      mockups.forEach((m) => m.classList.toggle('is-active', m.dataset.mockup === view));
      if (urlBar && URLS[view]) urlBar.textContent = URLS[view];
    }

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => setActiveView(tab.dataset.view));
    });

    // Header nav links ("Customer View" / "Organizer Hub") also jump to
    // the showcase and switch the active tab, since they share data-tab-target.
    document.querySelectorAll('[data-tab-target]').forEach((link) => {
      link.addEventListener('click', () => setActiveView(link.dataset.tabTarget));
    });
  }

  /* =======================================================
     3. 3D PERSPECTIVE TILT ON THE BROWSER-FRAME STAGE
     ======================================================= */
  function initTilt() {
    if (prefersReducedMotion) return;
    const frame = document.getElementById('browser-frame');
    const stage = document.getElementById('browser-stage');
    if (!frame || !stage) return;

    frame.addEventListener('mousemove', (e) => {
      const rect = frame.getBoundingClientRect();
      const xRelative = e.clientX - rect.left - rect.width / 2;
      const yRelative = e.clientY - rect.top - rect.height / 2;
      const rotateX = -yRelative / 30;
      const rotateY = xRelative / 30;
      stage.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });

    frame.addEventListener('mouseleave', () => {
      stage.style.transform = 'rotateX(0deg) rotateY(0deg)';
    });
  }

  /* =======================================================
     4. MOBILE NAV TOGGLE
     ======================================================= */
  function initNavToggle() {
    const toggle = document.getElementById('nav-toggle');
    const shell = document.querySelector('.nav-shell');
    if (!toggle || !shell) return;

    toggle.addEventListener('click', () => {
      const isOpen = shell.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(isOpen));
    });

    // Close the menu once a link inside it is used
    shell.querySelectorAll('.nav-links a, .nav-actions a').forEach((link) => {
      link.addEventListener('click', () => {
        shell.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* =======================================================
     5. "PORTAL WINDOWS" — scrolls to the showcase preview
     ======================================================= */
  function initPortalWindowsButton() {
    const btn = document.getElementById('portal-windows-btn');
    if (!btn) return;
    btn.addEventListener('click', () => {
      document.getElementById('showcase')?.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth' });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initParticleCanvas();
    initShowcaseTabs();
    initTilt();
    initNavToggle();
    initPortalWindowsButton();
  });

})();
