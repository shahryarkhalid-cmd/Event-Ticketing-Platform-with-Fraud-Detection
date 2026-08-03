/* ==========================================================================
   TIXORA — Customer Frontend Logic
   Vanilla JS only. Structured so backend calls can replace the MOCK_* data
   and the `api.*` stub functions without touching any DOM/UI code.
   ========================================================================== */
(() => {
  "use strict";

  /* --------------------------- Mock data layer --------------------------- */
  /* Replace with real Customer/Order/Event service calls. Shapes mirror
     the fields implied by Orders.py + Event/Ticket models so wiring later
     is a drop-in swap. */
  const MOCK_EVENTS = [
    {
      id: "EVT-1001", title: "Skyline Music Festival", category: "Music", city: "Austin", date: "2026-09-12", time: "18:00", venue: "Zilker Park Amphitheater", organizer: "Skyline Live", banner: "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=1200&auto=format&fit=crop", price: 45, seatsLeft: 8, trending: true, tiers: [
        { name: "VIP", price: 180, remaining: 6, color: "#F59E0B" },
        { name: "Premium", price: 95, remaining: 24, color: "#0B5ED7" },
        { name: "General", price: 45, remaining: 8, color: "#10B981" },
      ]
    },
    {
      id: "EVT-1002", title: "Startup Founders Summit", category: "Business", city: "San Francisco", date: "2026-08-02", time: "09:30", venue: "Moscone Center", organizer: "FoundersHub", banner: "https://images.unsplash.com/photo-1540575467063-178a50c2df87?q=80&w=1200&auto=format&fit=crop", price: 120, seatsLeft: 42, trending: false, tiers: [
        { name: "VIP", price: 350, remaining: 12, color: "#F59E0B" },
        { name: "General", price: 120, remaining: 42, color: "#10B981" },
      ]
    },
    {
      id: "EVT-1003", title: "Contemporary Art Expo", category: "Art", city: "New York", date: "2026-08-20", time: "11:00", venue: "The Highline Gallery", organizer: "ArtWorks NYC", banner: "https://images.unsplash.com/photo-1531058020387-3be344556be6?q=80&w=1200&auto=format&fit=crop", price: 25, seatsLeft: 3, trending: true, tiers: [
        { name: "Premium", price: 60, remaining: 10, color: "#0B5ED7" },
        { name: "General", price: 25, remaining: 3, color: "#10B981" },
      ]
    },
    {
      id: "EVT-1004", title: "Championship Fight Night", category: "Sports", city: "Las Vegas", date: "2026-10-04", time: "20:00", venue: "T-Mobile Arena", organizer: "Vegas Sports Group", banner: "https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=1200&auto=format&fit=crop", price: 89, seatsLeft: 56, trending: false, tiers: [
        { name: "VIP", price: 450, remaining: 8, color: "#F59E0B" },
        { name: "Premium", price: 210, remaining: 30, color: "#0B5ED7" },
        { name: "General", price: 89, remaining: 56, color: "#10B981" },
      ]
    },
    {
      id: "EVT-1005", title: "Stand-Up Comedy Night", category: "Comedy", city: "Chicago", date: "2026-08-15", time: "21:00", venue: "The Laugh Cellar", organizer: "Windy City Comedy", banner: "https://images.unsplash.com/photo-1585699324551-f6c309eedeca?q=80&w=1200&auto=format&fit=crop", price: 30, seatsLeft: 19, trending: false, tiers: [
        { name: "Premium", price: 55, remaining: 15, color: "#0B5ED7" },
        { name: "General", price: 30, remaining: 19, color: "#10B981" },
      ]
    },
    {
      id: "EVT-1006", title: "Tech & AI Conference", category: "Technology", city: "Austin", date: "2026-09-28", time: "08:00", venue: "Austin Convention Center", organizer: "DevSummit", banner: "https://images.unsplash.com/photo-1540575467063-178a50c2df87?q=80&w=1200&auto=format&fit=crop", price: 199, seatsLeft: 71, trending: true, tiers: [
        { name: "VIP", price: 599, remaining: 20, color: "#F59E0B" },
        { name: "Premium", price: 349, remaining: 40, color: "#0B5ED7" },
        { name: "General", price: 199, remaining: 71, color: "#10B981" },
      ]
    },
  ];

  const CATEGORIES = [
    { name: "Music", icon: "🎵", count: 128, color: "#EEF2FF" },
    { name: "Business", icon: "💼", count: 64, color: "#ECFDF5" },
    { name: "Art", icon: "🎨", count: 40, color: "#FFF7ED" },
    { name: "Sports", icon: "🏆", count: 96, color: "#FEF2F2" },
    { name: "Comedy", icon: "🎤", count: 33, color: "#F0F9FF" },
    { name: "Technology", icon: "💻", count: 57, color: "#F5F3FF" },
  ];

  const CITIES = [
    { name: "Austin", count: 210, img: "https://images.unsplash.com/photo-1531218150217-54595bc2b934?q=80&w=800&auto=format&fit=crop" },
    { name: "New York", count: 384, img: "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?q=80&w=800&auto=format&fit=crop" },
    { name: "San Francisco", count: 176, img: "https://images.unsplash.com/photo-1521747116042-5a810fda9664?q=80&w=800&auto=format&fit=crop" },
    { name: "Las Vegas", count: 129, img: "https://images.unsplash.com/photo-1605833556294-ea5c7a74f57d?q=80&w=800&auto=format&fit=crop" },
  ];

  // No longer used anywhere — bookings are now fetched live from
  // GET /orders/me (see api.getBookings / mapBookingFromBackend below).
  // Left in place rather than deleted, in case it's useful as a reference.
  const MOCK_BOOKINGS = [
    { id: "BK-88213", event: MOCK_EVENTS[0], tier: "Premium", qty: 2, total: 190, status: "confirmed", when: "upcoming" },
    { id: "BK-88117", event: MOCK_EVENTS[5], tier: "General", qty: 1, total: 199, status: "pending", when: "upcoming" },
    { id: "BK-87910", event: MOCK_EVENTS[2], tier: "General", qty: 3, total: 75, status: "cancelled", when: "previous" },
    { id: "BK-87650", event: MOCK_EVENTS[4], tier: "Premium", qty: 2, total: 110, status: "confirmed", when: "previous" },
  ];

  const MOCK_HOME_REVIEWS = [
    { name: "Jordan M.", event: "Skyline Music Festival", rating: 5, avatar: "https://i.pravatar.cc/80?img=5", text: "Sound quality across every stage was excellent, and entry with the digital ticket was instant." },
    { name: "Priya S.", event: "Tech & AI Conference", rating: 5, avatar: "https://i.pravatar.cc/80?img=32", text: "Registration took seconds and the fraud check gave me real peace of mind buying resale seats." },
    { name: "Marcus T.", event: "Championship Fight Night", rating: 4, avatar: "https://i.pravatar.cc/80?img=14", text: "Great seats, smooth entry. Booking multiple ticket tiers in one order made planning with friends easy." },
    { name: "Devon K.", event: "Stand-Up Comedy Night", rating: 5, avatar: "https://i.pravatar.cc/80?img=22", text: "Well organized from parking to re-entry. Already booked for next year." },
    { name: "Aisha R.", event: "Contemporary Art Expo", rating: 4, avatar: "https://i.pravatar.cc/80?img=45", text: "Loved being able to see live reviews before booking — set the right expectations." },
    { name: "Noah B.", event: "Startup Founders Summit", rating: 5, avatar: "https://i.pravatar.cc/80?img=51", text: "Clean checkout, real-time fraud screening, and my tickets were ready before I left the app." },
  ];

  const MOCK_NOTIFICATIONS = [
    { type: "confirmed", title: "Booking confirmed", body: "Your booking BK-88213 for Skyline Music Festival is confirmed.", time: "2h ago", unread: true },
    { type: "payment", title: "Payment successful", body: "$190.00 was charged for 2× Premium tickets.", time: "2h ago", unread: true },
    { type: "reminder", title: "Event reminder", body: "Startup Founders Summit starts in 3 days.", time: "1d ago", unread: false },
    { type: "updated", title: "Event updated", body: "Venue details changed for Tech & AI Conference.", time: "3d ago", unread: false },
    { type: "cancelled", title: "Event cancelled", body: "Contemporary Art Expo (Aug 20) was cancelled by the organizer.", time: "5d ago", unread: false },
    { type: "refund", title: "Refund processed", body: "$75.00 refunded to your original payment method.", time: "5d ago", unread: false },
  ];

  /* ------------------------------ API stubs ------------------------------ */
  const API_BASE = "http://localhost:8000";

  function authHeaders() {
    const token = localStorage.getItem("access_token");
    return { "Content-Type": "application/json", "Authorization": `Bearer ${token}` };
  }

  // FastAPI's 422 "detail" is often an array of {loc, msg, type} objects, not a
  // plain string — without this, `new Error(detail)` renders as "[object Object]"
  // and hides the real reason. Mirrors the same helper in login.js/signup.js.
  function formatErrorDetail(detail) {
    if (!detail) return "";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => {
        if (typeof d === "string") return d;
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
        return field ? `${field}: ${d.msg}` : (d.msg || JSON.stringify(d));
      }).join("; ");
    }
    if (typeof detail === "object") return detail.msg || JSON.stringify(detail);
    return String(detail);
  }

  const TIER_COLORS = { VIP: "#F59E0B", Premium: "#0B5ED7", General: "#10B981", VVIP: "#8B5CF6" };

  // backend Event + TicketTier[] -> shape this file's rendering code expects
  function mapEventFromBackend(evt, tiers) {
    tiers = Array.isArray(tiers) ? tiers : [];
    const [date] = (evt.start_datetime || "").split("T");
    const time = (evt.start_datetime || "").split("T")[1]?.slice(0, 5) || "";
    const lowestPrice = tiers.length ? Math.min(...tiers.map(t => t.price)) : 0;
    const totalRemaining = tiers.reduce((s, t) => s + (t.total_seats - t.sold_quantity), 0);

    return {
      id: String(evt.id),
      title: evt.name,
      category: evt.category,
      city: evt.city,
      country: evt.country,
      date,
      time,
      venue: evt.venue,
      organizer: "", // no organizer name on Event yet — see note below
      banner: evt.banner_url || "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=1200&auto=format&fit=crop",
      price: lowestPrice,
      seatsLeft: totalRemaining,
      trending: false, // not implemented on backend
      tiers: tiers.map(t => ({
        id: t.id,
        name: t.category_name,
        price: t.price,
        remaining: t.total_seats - t.sold_quantity,
        color: TIER_COLORS[t.category_name] || "#6B7280"
      }))
    };
  }

  // backend Order -> shape bookingCardHTML()/renderBookings() expect.
  // The exact OrderRead schema isn't visible from the frontend alone, so this
  // reads a handful of plausible field names defensively (mirrors the same
  // approach used in payment-result.js's readOrderFields).
  function mapBookingFromBackend(order, eventsById) {
    const items = Array.isArray(order.items) ? order.items : (order.item ? [order.item] : []);
    const firstItem = items[0] || {};
    const eventId = order.event_id ?? order.event?.id ?? firstItem.event_id;
    const matchedEvent = eventsById && eventId != null ? eventsById[String(eventId)] : null;

    const tierName = firstItem.tier_name || firstItem.category_name || firstItem.name || order.tier_name || "General";
    const qty = items.length
      ? items.reduce((s, i) => s + Number(i.quantity ?? i.qty ?? 0), 0)
      : Number(order.quantity ?? order.ticket_quantity ?? 1);

    const total = order.total_amount ?? order.amount ?? order.total_price ?? order.total ?? 0;
    const rawStatus = String(order.status || order.payment_status || "pending").toLowerCase();
    const status = rawStatus === "paid" || rawStatus === "confirmed" ? "confirmed"
      : (rawStatus === "cancelled" || rawStatus === "canceled" || rawStatus === "failed") ? "cancelled"
        : "pending";

    const eventTitle = matchedEvent?.title || order.event?.name || order.event?.title || order.event_name || "Event";
    const eventBanner = matchedEvent?.banner || order.event?.banner_url
      || "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=1200&auto=format&fit=crop";
    const eventDate = matchedEvent?.date || (order.event?.start_datetime || "").split("T")[0];

    const when = eventDate && new Date(eventDate) < new Date(new Date().toDateString()) ? "previous" : "upcoming";

    return {
      id: `ORD-${order.id ?? order.order_id ?? ""}`,
      orderId: order.id ?? order.order_id,
      event: { title: eventTitle, banner: eventBanner },
      tier: tierName,
      qty,
      total: Number(total) || 0,
      status,
      when
    };
  }

  const api = {
    getEvents: async () => {
      const res = await fetch(`${API_BASE}/events/customer`);
      if (!res.ok) {
        let bodyText = "";
        try { bodyText = await res.text(); } catch (e) { /* ignore */ }
        console.error(`GET /events/customer → ${res.status}${bodyText ? `: ${bodyText}` : ""}`);
        throw new Error(`Events request failed (${res.status})`);
      }
      const rawEvents = await res.json();
      // Use allSettled so one event with a broken/forbidden tiers request
      // doesn't take down the entire list — it just shows with no tiers.
      const settled = await Promise.allSettled(rawEvents.map(async (evt) => {
        const tRes = await fetch(`${API_BASE}/events/${evt.id}/ticket-tiers`, { headers: authHeaders() });
        const tiers = tRes.ok ? await tRes.json() : [];
        return mapEventFromBackend(evt, tiers);
      }));
      return settled
        .filter((r) => {
          if (r.status === "rejected") console.warn("Skipped one event — couldn't map it:", r.reason);
          return r.status === "fulfilled";
        })
        .map(r => r.value);
    },
    getBookings: async (events) => {
      const res = await fetch(`${API_BASE}/orders/me`, { headers: authHeaders() });
      if (!res.ok) throw new Error("Couldn't load bookings");
      const orders = await res.json();
      const eventsById = {};
      (events || []).forEach((e) => { eventsById[String(e.id)] = e; });
      return Array.isArray(orders) ? orders.map((o) => mapBookingFromBackend(o, eventsById)) : [];
    },
    createOrder: async (payload) => {
      const res = await fetch(`${API_BASE}/orders`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          event_id: Number(payload.eventId),
          items: payload.items.map(i => ({
            ticket_tier_id: i.tierId,
            quantity: i.qty
          }))
        })
      });
      if (!res.ok) {
        let detail = "";
        try { const errBody = await res.json(); detail = formatErrorDetail(errBody.detail); } catch (e) { /* body wasn't JSON */ }
        console.error(`POST /orders → ${res.status}${detail ? `: ${detail}` : ""}`);
        throw new Error(detail || `Order request failed (${res.status})`);
      }
      const order = await res.json();
      return { orderId: order.id, ...payload };
    },
  };
  const wait = (ms) => new Promise((res) => setTimeout(res, ms));

  /* ------------------------------- State ---------------------------------- */
  const state = {
    currentUser: null,
    events: [],
    bookings: [],
    filters: { q: "", category: "all", country: "all", city: "", dateFrom: "", dateTo: "", price: "all", time: "all", sort: "popular" },
    page: 1,
    perPage: 6,
    wishlist: new Set(["EVT-1003"]),
    activeModalEvent: null,
    cart: {}, // { tierName: qty } for the event currently open in the quick ticket modal
  };

  const money = (n) => "$" + n.toFixed(2);
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  /* ------------------------------ Toasts ---------------------------------- */
  function toast(title, body, kind = "ok") {
    const stack = $("#toastStack");
    if (!stack) return;
    const el = document.createElement("div");
    el.className = "toast" + (kind === "warn" ? " warn" : kind === "err" ? " err" : "");
    el.innerHTML = `<div><strong>${escapeHTML(title)}</strong><p>${escapeHTML(body)}</p></div>`;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity 300ms ease, transform 300ms ease";
      el.style.opacity = "0";
      el.style.transform = "translateX(24px)";
      setTimeout(() => el.remove(), 300);
    }, 3800);
  }

  function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
  }

  /* ------------------------------ Identity --------------------------------- */
  // Fills every on-screen spot that shows the user's name/email with the
  // name they actually gave at signup (full_name from /users/me) — the
  // profile card heading, the profile form's "Full name"/"Email" fields.
  function applyCustomerIdentity(user) {
    if (!user) return;
    const name = user.full_name || "";
    const email = user.email || "";

    const nameDisplay = $("#profileNameDisplay");
    if (nameDisplay) nameDisplay.textContent = name;

    const emailDisplay = $("#profileEmailDisplay");
    if (emailDisplay) emailDisplay.textContent = email;

    const nameInput = $("#fullName");
    if (nameInput) nameInput.value = name;

    const emailInput = $("#emailField");
    if (emailInput) emailInput.value = email;
  }

  /* ------------------------------ Ripple ---------------------------------- */
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn");
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement("span");
    const size = Math.max(rect.width, rect.height);
    ripple.className = "ripple";
    ripple.style.width = ripple.style.height = size + "px";
    ripple.style.left = e.clientX - rect.left - size / 2 + "px";
    ripple.style.top = e.clientY - rect.top - size / 2 + "px";
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 650);
  });

  /* ------------------------------- Navbar --------------------------------- */
  function initNavbar() {
    const nav = $("#navbar");
    if (nav) {
      window.addEventListener("scroll", () => {
        nav.classList.toggle("is-scrolled", window.scrollY > 8);
      }, { passive: true });
    }

    const toggle = $("#menuToggle");
    const drawer = $("#mobileDrawer");
    const close = () => { drawer?.classList.remove("open"); toggle?.classList.remove("open"); };
    toggle?.addEventListener("click", () => {
      const willOpen = !drawer.classList.contains("open");
      drawer.classList.toggle("open", willOpen);
      toggle.classList.toggle("open", willOpen);
    });
    $("#drawerOverlay")?.addEventListener("click", close);
    $("#drawerClose")?.addEventListener("click", close);
    $$(".drawer-panel .nav-link").forEach((l) => l.addEventListener("click", close));

    $$("[data-goto-support]").forEach((el) => el.addEventListener("click", (e) => {
      e.preventDefault(); close();
      toast("Customer support", "Our help center would open here — chat, FAQs and ticket status.", "ok");
    }));
    $$("[data-goto-about]").forEach((el) => el.addEventListener("click", (e) => {
      e.preventDefault(); close();
      toast("About Tixora", "AI-powered event ticketing with real-time fraud protection.", "ok");
    }));
    $$("[data-goto-legal]").forEach((el) => el.addEventListener("click", (e) => {
      e.preventDefault(); close();
      toast("Terms & Privacy", "Legal documents would open here.", "ok");
    }));
  }

  /* --------------------------- View / tab routing -------------------------- */
  function initViews() {
    const views = $$(".view");
    const navLinks = $$(".nav-link[data-view]");
    const bottomTabs = $$(".bottom-tab[data-view]");
    function showView(name) {
      views.forEach((v) => v.classList.toggle("hidden", v.dataset.view !== name));
      navLinks.forEach((l) => l.classList.toggle("active", l.dataset.view === name));
      bottomTabs.forEach((t) => t.classList.toggle("active", t.dataset.view === name));
      window.scrollTo({ top: 0, behavior: "smooth" });
      const active = document.querySelector(`.view[data-view="${name}"]`);
      active?.classList.remove("page-view");
      void active?.offsetWidth; // restart animation
      active?.classList.add("page-view");
    }

    navLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        showView(link.dataset.view);
      });
    });

    bottomTabs.forEach((tab) => {
      tab.addEventListener("click", (e) => {
        e.preventDefault();
        showView(tab.dataset.view);
      });
    });

    $$("[data-goto]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        showView(el.dataset.goto);
      });
    });

    showView("home");
  }

  /* ------------------------------ Animated counters ------------------------ */
  function initCounters() {
    const counters = $$(".stat-num, .stat-value");
    if (!counters.length) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.dataset.count || el.textContent, 10);
        if (Number.isNaN(target)) return;
        let cur = 0;
        const step = Math.max(1, Math.ceil(target / 60));
        const tick = () => {
          cur = Math.min(target, cur + step);
          el.textContent = cur.toLocaleString() + (el.dataset.suffix || "");
          if (cur < target) requestAnimationFrame(tick);
        };
        tick();
        io.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach((c) => io.observe(c));
  }

  /* --------------------------- Search suggestions -------------------------- */
  function initSearchSuggestions() {
    const input = $("#heroSearchInput");
    const box = $("#searchSuggestions");
    if (!input || !box) return;

    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      if (!q) { box.classList.remove("show"); return; }
      const matches = state.events.filter((ev) => ev.title.toLowerCase().includes(q) || ev.city.toLowerCase().includes(q)).slice(0, 5);
      if (!matches.length) {
        box.innerHTML = `<div class="suggestion-item text-muted">No matches for "${escapeHTML(input.value)}"</div>`;
      } else {
        box.innerHTML = matches.map((ev) => `
          <div class="suggestion-item" data-id="${ev.id}" role="option" tabindex="0">
            <span>🔎</span><span>${escapeHTML(ev.title)} — <span class="text-muted">${escapeHTML(ev.city)}</span></span>
          </div>`).join("");
      }
      box.classList.add("show");
    });

    box.addEventListener("click", (e) => {
      const item = e.target.closest(".suggestion-item[data-id]");
      if (!item) return;
      input.value = "";
      box.classList.remove("show");
      const ev = state.events.find((x) => x.id === item.dataset.id);
      if (ev) openTicketModal(ev.id);
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".search-field") && !e.target.closest("#searchSuggestions")) {
        box.classList.remove("show");
      }
    });

    $("#heroSearchBtn")?.addEventListener("click", () => {
      state.filters.q = input.value.trim();
      const heroCity = $("#heroCity")?.value;
      if (heroCity && heroCity !== "Any city") state.filters.city = heroCity;
      document.querySelector('.nav-link[data-view="browse"]')?.click();
      if ($("#filterSearch")) $("#filterSearch").value = state.filters.q;
      if ($("#filterCity") && heroCity && heroCity !== "Any city") $("#filterCity").value = heroCity;
      state.page = 1;
      renderEvents();
    });
  }

  /* --------------------------------- Filters -------------------------------- */
  function initFilters() {
    const catSel = $("#filterCategory");
    const countrySel = $("#filterCountry");
    const cityInp = $("#filterCity");
    const dateFromInp = $("#filterDateFrom");
    const dateToInp = $("#filterDateTo");
    const priceSel = $("#filterPrice");
    const sortSel = $("#sortSelect");
    const searchInp = $("#filterSearch");
    const clearBtn = $("#filtersClear");

    const bind = (el, key, evt = "change") => {
      el?.addEventListener(evt, () => {
        state.filters[key] = el.value;
        state.page = 1;
        renderEvents();
      });
    };
    bind(catSel, "category");
    bind(countrySel, "country");
    bind(cityInp, "city", "input");
    bind(dateFromInp, "dateFrom");
    bind(dateToInp, "dateTo");
    bind(priceSel, "price");
    bind(sortSel, "sort");
    bind(searchInp, "q", "input");

    $$(".time-chip[data-time]").forEach((chip) => {
      chip.addEventListener("click", () => {
        $$(".time-chip[data-time]").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        state.filters.time = chip.dataset.time;
        state.page = 1;
        renderEvents();
      });
    });

    clearBtn?.addEventListener("click", () => {
      state.filters = { q: "", category: "all", country: "all", city: "", dateFrom: "", dateTo: "", price: "all", time: "all", sort: "popular" };
      if (catSel) catSel.value = "all";
      if (countrySel) countrySel.value = "all";
      if (cityInp) cityInp.value = "";
      if (dateFromInp) dateFromInp.value = "";
      if (dateToInp) dateToInp.value = "";
      if (priceSel) priceSel.value = "all";
      if (sortSel) sortSel.value = "popular";
      if (searchInp) searchInp.value = "";
      $$(".time-chip[data-time]").forEach((c) => c.classList.toggle("active", c.dataset.time === "all"));
      $$(".tab-chip[data-cat]").forEach((c) => c.classList.toggle("active", c.dataset.cat === "all"));
      state.page = 1;
      renderEvents();
    });

    $$(".tab-chip[data-cat]").forEach((chip) => {
      chip.addEventListener("click", () => {
        $$(".tab-chip[data-cat]").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        state.filters.category = chip.dataset.cat;
        if (catSel) catSel.value = chip.dataset.cat;
        state.page = 1;
        renderEvents();
      });
    });
  }

  const FILTER_LABELS = {
    q: (v) => `Search: "${v}"`,
    category: (v) => `Category: ${v}`,
    country: (v) => `Country: ${v}`,
    city: (v) => `City: ${v}`,
    dateFrom: (v) => `From ${v}`,
    dateTo: (v) => `To ${v}`,
    price: (v) => ({ under50: "Under $50", "50-150": "$50–$150", over150: "$150+" }[v] || v),
    time: (v) => `Time: ${v[0].toUpperCase()}${v.slice(1)}`,
  };
  const FILTER_DEFAULTS = { q: "", category: "all", country: "all", city: "", dateFrom: "", dateTo: "", price: "all", time: "all" };

  function renderActiveChips() {
    const box = $("#activeFilterChips");
    if (!box) return;
    const f = state.filters;
    const active = Object.keys(FILTER_DEFAULTS).filter((k) => f[k] && f[k] !== FILTER_DEFAULTS[k]);
    if (!active.length) { box.innerHTML = ""; return; }
    box.innerHTML = active.map((k) => `<span class="filter-chip">${escapeHTML(FILTER_LABELS[k](f[k]))}<button type="button" data-clear="${k}" aria-label="Remove filter">✕</button></span>`).join("");
    $$("[data-clear]", box).forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.clear;
        state.filters[key] = FILTER_DEFAULTS[key];
        const idMap = { q: "#filterSearch", category: "#filterCategory", country: "#filterCountry", city: "#filterCity", dateFrom: "#filterDateFrom", dateTo: "#filterDateTo", price: "#filterPrice", time: null };
        const el = idMap[key] && $(idMap[key]);
        if (el) el.value = FILTER_DEFAULTS[key];
        if (key === "time") $$(".time-chip[data-time]").forEach((c) => c.classList.toggle("active", c.dataset.time === "all"));
        if (key === "category") $$(".tab-chip[data-cat]").forEach((c) => c.classList.toggle("active", c.dataset.cat === "all"));
        state.page = 1;
        renderEvents();
      });
    });
  }

  function timeBucket(hhmm) {
    const h = parseInt(hhmm.split(":")[0], 10);
    if (h < 12) return "morning";
    if (h < 17) return "afternoon";
    return "evening";
  }

  function applyFilters(list) {
    let out = list.slice();
    const f = state.filters;
    if (f.q) out = out.filter((ev) => ev.title.toLowerCase().includes(f.q.toLowerCase()));
    if (f.category && f.category !== "all") out = out.filter((ev) => ev.category === f.category);
    if (f.country && f.country !== "all") out = out.filter((ev) => (ev.country || "United States") === f.country);
    if (f.city && f.city.trim()) out = out.filter((ev) => ev.city.toLowerCase().includes(f.city.trim().toLowerCase()));
    if (f.dateFrom) out = out.filter((ev) => ev.date >= f.dateFrom);
    if (f.dateTo) out = out.filter((ev) => ev.date <= f.dateTo);
    if (f.time && f.time !== "all") out = out.filter((ev) => timeBucket(ev.time) === f.time);
    if (f.price && f.price !== "all") {
      out = out.filter((ev) => {
        if (f.price === "under50") return ev.price < 50;
        if (f.price === "50-150") return ev.price >= 50 && ev.price <= 150;
        if (f.price === "over150") return ev.price > 150;
        return true;
      });
    }
    if (f.sort === "price-asc") out.sort((a, b) => a.price - b.price);
    else if (f.sort === "price-desc") out.sort((a, b) => b.price - a.price);
    else if (f.sort === "date") out.sort((a, b) => new Date(a.date) - new Date(b.date));
    else if (f.sort === "seats") out.sort((a, b) => a.seatsLeft - b.seatsLeft);
    return out;
  }

  /* -------------------------------- Cards ---------------------------------- */
  function eventCardHTML(ev) {
    const isWished = state.wishlist.has(ev.id);
    const low = ev.seatsLeft <= 10;
    const dateFmt = new Date(ev.date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
    return `
    <article class="event-card" data-id="${ev.id}" tabindex="0" role="button" aria-label="View ${escapeHTML(ev.title)}">
      <div class="event-card-media">
        <img src="${ev.banner}" alt="${escapeHTML(ev.title)}" loading="lazy">
        ${ev.trending ? '<span class="card-badge trending">🔥 Trending</span>' : `<span class="card-badge">${escapeHTML(ev.category)}</span>`}
        <button class="wishlist-toggle ${isWished ? "active" : ""}" data-wish="${ev.id}" aria-label="Toggle wishlist" aria-pressed="${isWished}">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="${isWished ? "currentColor" : "none"}" stroke="currentColor" stroke-width="2"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"/></svg>
        </button>
      </div>
      <div class="event-card-body">
        <div class="event-card-date">${dateFmt} · ${ev.time}</div>
        <h3 class="event-card-title">${escapeHTML(ev.title)}</h3>
        <div class="event-card-meta">
          <span class="row">📍 ${escapeHTML(ev.venue)}, ${escapeHTML(ev.city)}</span>
          <span class="row">🎟️ by ${escapeHTML(ev.organizer)}</span>
        </div>
        <div class="event-card-tear"></div>
      </div>
      <div class="event-card-footer">
        <div class="event-card-price">${money(ev.price)}<small>starting price</small></div>
        <div class="seats-left ${low ? "low" : ""}">${ev.seatsLeft} seats left</div>
      </div>
    </article>`;
  }

  function bindCardEvents(container) {
    $$(".event-card", container).forEach((card) => {
      card.addEventListener("click", (e) => {
        if (e.target.closest("[data-wish]")) return;
        openTicketModal(card.dataset.id);
      });
      card.addEventListener("keydown", (e) => {
        if ((e.key === "Enter" || e.key === " ") && !e.target.closest("[data-wish]")) {
          e.preventDefault();
          openTicketModal(card.dataset.id);
        }
      });
    });
    $$("[data-wish]", container).forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleWishlist(btn.dataset.wish, btn);
      });
    });
  }

  function toggleWishlist(id, btnEl) {
    const ev = state.events.find((x) => x.id === id);
    if (!ev) return;
    const nowActive = !state.wishlist.has(id);
    if (nowActive) state.wishlist.add(id); else state.wishlist.delete(id);
    $$(`[data-wish="${id}"]`).forEach((b) => {
      b.classList.toggle("active", nowActive);
      b.setAttribute("aria-pressed", String(nowActive));
      b.querySelector("svg")?.setAttribute("fill", nowActive ? "currentColor" : "none");
    });
    toast(nowActive ? "Added to wishlist" : "Removed from wishlist", ev.title, nowActive ? "ok" : "warn");
    if ($("#view-wishlist")) renderWishlist();
  }

  /* ------------------------------ Renderers --------------------------------- */
  function renderFeatured() {
    const el = $("#featuredGrid");
    if (!el) return;
    // "Newest events first" — the backend doesn't yet return a created_at
    // timestamp for events, so this uses the numeric id as a stand-in
    // (higher id = created more recently, since ids are auto-incrementing).
    // Swap this for a real `evt.createdAt` sort the moment the backend adds one.
    const newestFirst = state.events.slice().sort((a, b) => Number(b.id) - Number(a.id));
    el.innerHTML = newestFirst.slice(0, 3).map(eventCardHTML).join("");
    bindCardEvents(el);
  }

  function renderTrending() {
    const el = $("#trendingGrid");
    if (!el) return;
    el.innerHTML = state.events.filter((e) => e.trending).map(eventCardHTML).join("");
    bindCardEvents(el);
  }

  function renderUpcoming() {
    const el = $("#upcomingGrid");
    if (!el) return;
    const sorted = state.events.slice().sort((a, b) => new Date(a.date) - new Date(b.date));
    el.innerHTML = sorted.slice(0, 3).map(eventCardHTML).join("");
    bindCardEvents(el);
  }

  function renderCategories() {
    const el = $("#categoriesGrid");
    if (!el) return;
    el.innerHTML = CATEGORIES.map((c) => `
      <a class="cat-tile" href="#" data-goto="browse" data-cat-jump="${c.name}">
        <div class="cat-icon" style="background:${c.color}">${c.icon}</div>
        <span>${c.name}</span>
        <small>${c.count} events</small>
      </a>`).join("");
    el.querySelectorAll("[data-cat-jump]").forEach((tile) => {
      tile.addEventListener("click", () => {
        state.filters.category = tile.dataset.catJump;
        const sel = $("#filterCategory");
        if (sel) sel.value = tile.dataset.catJump;
      });
    });
  }

  function renderCities() {
    const el = $("#citiesGrid");
    if (!el) return;
    el.innerHTML = CITIES.map((c) => `
      <a class="city-tile" href="#" data-goto="browse" data-city-jump="${c.name}">
        <img src="${c.img}" alt="${c.name}" loading="lazy">
        <div class="city-tile-label"><strong>${c.name}</strong><span>${c.count} events</span></div>
      </a>`).join("");
    el.querySelectorAll("[data-city-jump]").forEach((tile) => {
      tile.addEventListener("click", () => {
        state.filters.city = tile.dataset.cityJump;
        const sel = $("#filterCity");
        if (sel) sel.value = tile.dataset.cityJump;
      });
    });
  }

  function renderEvents() {
    const grid = $("#browseGrid");
    const emptyState = $("#browseEmpty");
    const meta = $("#resultsMeta");
    const pager = $("#pagination");
    if (!grid) return;

    const filtered = applyFilters(state.events);
    renderActiveChips();
    const totalPages = Math.max(1, Math.ceil(filtered.length / state.perPage));
    state.page = Math.min(state.page, totalPages);
    const start = (state.page - 1) * state.perPage;
    const pageItems = filtered.slice(start, start + state.perPage);

    if (meta) meta.querySelector("span").textContent = `${filtered.length} event${filtered.length === 1 ? "" : "s"} found`;

    if (!filtered.length) {
      grid.innerHTML = "";
      emptyState?.classList.remove("hidden");
      pager && (pager.innerHTML = "");
      return;
    }
    emptyState?.classList.add("hidden");
    grid.innerHTML = pageItems.map(eventCardHTML).join("");
    bindCardEvents(grid);
    renderPagination(totalPages);
  }

  function renderPagination(totalPages) {
    const pager = $("#pagination");
    if (!pager) return;
    let html = `<button class="page-btn" data-page="${state.page - 1}" ${state.page === 1 ? "disabled" : ""} aria-label="Previous page">‹</button>`;
    for (let i = 1; i <= totalPages; i++) {
      html += `<button class="page-btn ${i === state.page ? "active" : ""}" data-page="${i}">${i}</button>`;
    }
    html += `<button class="page-btn" data-page="${state.page + 1}" ${state.page === totalPages ? "disabled" : ""} aria-label="Next page">›</button>`;
    pager.innerHTML = html;
    $$(".page-btn", pager).forEach((btn) => {
      btn.addEventListener("click", () => {
        const p = parseInt(btn.dataset.page, 10);
        if (Number.isNaN(p) || p < 1 || p > totalPages) return;
        state.page = p;
        renderEvents();
        $("#browseGrid")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function renderWishlist() {
    const grid = $("#wishlistGrid");
    const empty = $("#wishlistEmpty");
    if (!grid) return;
    const items = state.events.filter((ev) => state.wishlist.has(ev.id));
    if (!items.length) {
      grid.innerHTML = "";
      empty?.classList.remove("hidden");
      return;
    }
    empty?.classList.add("hidden");
    grid.innerHTML = items.map(eventCardHTML).join("");
    bindCardEvents(grid);
  }

  /* ---------------------------- Quick Ticket Modal -------------------------- */
  function openTicketModal(id) {
    const ev = state.events.find((x) => x.id === id);
    if (!ev) return;
    state.activeModalEvent = ev;
    state.cart = {};
    ev.tiers.forEach((t) => { state.cart[t.id] = 0; });

    $("#modalBanner").src = ev.banner;
    $("#modalBanner").alt = ev.title;
    $("#modalEventTitle").textContent = ev.title;
    const dateFmt = new Date(ev.date + "T00:00:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" });
    $("#modalEventDate").textContent = `${dateFmt} · ${ev.time} · ${ev.venue}`;
    $("#modalEventDesc").textContent = `Join ${ev.organizer} for ${ev.title} in ${ev.city}. Mix and match ticket classes and quantities into a single order below.`;

    renderClassList();
    updatePriceSummary();

    const overlay = $("#ticketModal");
    overlay.classList.add("open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    setTimeout(() => $("#modalCloseBtn")?.focus(), 50);
  }

  function closeTicketModal() {
    const overlay = $("#ticketModal");
    overlay.classList.remove("open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function renderClassList() {
    const list = $("#classList");
    const ev = state.activeModalEvent;
    list.innerHTML = ev.tiers.map((tier) => {
      const soldout = tier.remaining <= 0;
      const qty = state.cart[tier.id] || 0;
      return `
      <div class="class-row ${qty > 0 ? "has-qty" : ""} ${soldout ? "soldout" : ""}" data-tier="${tier.id}">
        <div class="class-left">
          <span class="class-dot" style="background:${tier.color}"></span>
          <div>
            <div class="class-name">${tier.name}</div>
            <div class="class-desc">${soldout ? "Sold out" : tier.remaining + " remaining"}</div>
          </div>
        </div>
        <div class="class-right">
          <span class="class-price">${money(tier.price)}</span>
          <div class="stepper">
            <button type="button" class="st-minus" data-act="minus" data-tier="${tier.id}" ${qty <= 0 ? "disabled" : ""} aria-label="Decrease ${tier.name} quantity">−</button>
            <span class="stepper-val">${qty}</span>
            <button type="button" class="st-plus" data-act="plus" data-tier="${tier.id}" ${soldout || qty >= tier.remaining ? "disabled" : ""} aria-label="Increase ${tier.name} quantity">+</button>
          </div>
        </div>
      </div>`;
    }).join("");
    $$("[data-act]", list).forEach((btn) => {
      btn.addEventListener("click", () => {
        const tierId = Number(btn.dataset.tier);
        const tier = ev.tiers.find((t) => t.id === tierId);
        const cur = state.cart[tierId] || 0;
        if (btn.dataset.act === "plus") {
          if (cur >= tier.remaining) { $("#qtyWarning").textContent = `Only ${tier.remaining} ${tier.name} tickets remaining.`; return; }
          state.cart[tierId] = cur + 1;
        } else {
          state.cart[tierId] = Math.max(0, cur - 1);
        }
        $("#qtyWarning").textContent = "";
        renderClassList();
        updatePriceSummary();
      });
    });
  }

  function renderCartItems() {
    const box = $("#cartItems");
    const ev = state.activeModalEvent;
    const entries = ev.tiers
      .map((t) => ({ ...t, qty: state.cart[t.id] || 0 }))
      .filter((t) => t.qty > 0);
    if (!entries.length) {
      box.innerHTML = `<p class="ticket-cart-empty">No tickets added yet — pick a quantity above.</p>`;
      return;
    }
    box.innerHTML = entries.map((t) => `
      <div class="cart-item">
        <span class="ci-name"><span class="ci-dot" style="background:${t.color}"></span>${t.name} × ${t.qty}</span>
        <span class="ci-right">${money(t.price * t.qty)}<button type="button" class="ci-remove" data-remove="${t.id}" aria-label="Remove ${t.name}">✕</button></span>
      </div>`).join("");
    $$("[data-remove]", box).forEach((btn) => {
      btn.addEventListener("click", () => {
        state.cart[btn.dataset.remove] = 0;
        renderClassList();
        updatePriceSummary();
      });
    });
  }

  function updatePriceSummary() {
    renderCartItems();
    const ev = state.activeModalEvent;
    const entries = ev.tiers.map((t) => ({ ...t, qty: state.cart[t.id] || 0 })).filter((t) => t.qty > 0);
    const totalQty = entries.reduce((s, t) => s + t.qty, 0);
    const subtotal = entries.reduce((s, t) => s + t.price * t.qty, 0);
    const fees = subtotal > 0 ? +(subtotal * 0.06).toFixed(2) : 0;
    const total = +(subtotal + fees).toFixed(2);

    $("#sumSubtotal").textContent = money(subtotal);
    $("#sumQty").textContent = String(totalQty);
    $("#sumFees").textContent = money(fees);
    $("#sumTotal").textContent = money(total);

    $("#proceedBtn").disabled = entries.length === 0;
  }

  function initModal() {
    $("#modalCloseBtn")?.addEventListener("click", closeTicketModal);
    $("#ticketModal")?.addEventListener("click", (e) => {
      if (e.target.id === "ticketModal") closeTicketModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && $("#ticketModal")?.classList.contains("open")) closeTicketModal();
    });
    $("#proceedBtn")?.addEventListener("click", async () => {
      const btn = $("#proceedBtn");
      const ev = state.activeModalEvent;
      if (!ev) return;
      const entries = ev.tiers.map((t) => ({ ...t, qty: state.cart[t.id] || 0 })).filter((t) => t.qty > 0);
      if (!entries.length) return;
      const originalHTML = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span> Creating order…`;
      try {
        const order = await api.createOrder({
          eventId: ev.id,
          items: entries.map((t) => ({ tierId: t.id, tierName: t.name, qty: t.qty, price: t.price })),
          total: parseFloat($("#sumTotal").textContent.replace("$", "")),
        });
        toast("Order created", `${order.orderId} — proceed to payment.`, "ok");
        closeTicketModal();
        goToPaymentSummary(ev, entries, $("#sumTotal").textContent, order.orderId);

        // Refresh bookings in the background so this order shows up in
        // My Bookings right away, without waiting for a full page reload.
        api.getBookings(state.events)
          .then((bookings) => { state.bookings = bookings; renderBookings(); })
          .catch((e) => console.error("Couldn't refresh bookings:", e));
      } catch (err) {
        console.error("Order creation failed:", err);
        toast("Order failed", err.message || "Something went wrong. Please try again.", "err");
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    });
  }

  /* -------------------------------- Payment view ----------------------------- */
  function goToPaymentSummary(ev, items, totalStr, orderId) {
    document.querySelector('.nav-link[data-view="payment"]')?.click();
    $("#paySummaryEvent").textContent = ev.title;
    $("#paySummaryMeta").textContent = `${new Date(ev.date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })} · ${ev.venue}, ${ev.city}`;
    const totalQty = items.reduce((s, i) => s + i.qty, 0);
    $("#paySummaryQty").textContent = String(totalQty);
    $("#paySummaryTotal").textContent = totalStr;
    $("#paySummaryOrderId").textContent = orderId;
    $("#paySummaryItems").innerHTML = items.map((i) => `
      <div class="price-row"><span>${escapeHTML(i.name)} × ${i.qty}</span><span>${money(i.price * i.qty)}</span></div>`).join("");
    resetPaymentState();
  }

  function resetPaymentState() {
    $("#payIdle")?.classList.remove("hidden");
    $("#payLoading")?.classList.add("hidden");
    $("#paySuccess")?.classList.add("hidden");
    $("#payFailed")?.classList.add("hidden");
  }

  function initPayment() {
    $$(".pay-method").forEach((m) => {
      m.addEventListener("click", () => {
        $$(".pay-method").forEach((x) => x.classList.remove("selected"));
        m.classList.add("selected");
      });
    });
    $("#confirmPaymentBtn")?.addEventListener("click", async () => {
      $("#payIdle").classList.add("hidden");
      $("#payLoading").classList.remove("hidden");

      const orderId = $("#paySummaryOrderId").textContent;

      try {
        const res = await fetch(`${API_BASE}/orders/${orderId}/checkout`, {
          method: "POST",
          headers: authHeaders()
        });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          const detail = formatErrorDetail(data.detail);
          console.error(`POST /orders/${orderId}/checkout → ${res.status}${detail ? `: ${detail}` : ""}`);
          throw new Error(detail || `Could not start checkout (${res.status})`);
        }

        // Redirect the whole page to Stripe's hosted checkout
        window.location.href = data.url || data.checkout_url;

      } catch (err) {
        console.error("Checkout failed:", err);
        $("#payLoading").classList.add("hidden");
        $("#payFailed").classList.remove("hidden");
        toast("Payment failed", err.message, "err");
      }
    });
    $("#retryPaymentBtn")?.addEventListener("click", resetPaymentState);
  }

  async function payNowFromBookings(btn) {
    const orderId = btn.dataset.paynow;
    if (!orderId) return;
    const originalLabel = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Redirecting…";
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/checkout`, {
        method: "POST",
        headers: authHeaders()
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = formatErrorDetail(data.detail);
        console.error(`POST /orders/${orderId}/checkout → ${res.status}${detail ? `: ${detail}` : ""}`);
        throw new Error(detail || `Could not start checkout (${res.status})`);
      }
      // Redirect to Stripe; Stripe sends the user back to the payment
      // confirmation page (payment-result.html) once they're done.
      window.location.href = data.url || data.checkout_url;
    } catch (err) {
      console.error("Pay Now failed:", err);
      btn.disabled = false;
      btn.textContent = originalLabel;
      toast("Payment failed", err.message, "err");
    }
  }

  /* -------------------------------- Bookings -------------------------------- */
  function bookingCardHTML(b) {
    const statusLabel = { confirmed: "Confirmed", pending: "Pending", cancelled: "Cancelled" }[b.status];
    const icon = { confirmed: "✓", pending: "…", cancelled: "✕" }[b.status];
    return `
    <div class="booking-card">
      <div class="booking-media"><img src="${b.event.banner}" alt="${escapeHTML(b.event.title)}" loading="lazy"></div>
      <div class="booking-info">
        <h4>${escapeHTML(b.event.title)}</h4>
        <div class="booking-meta">
          <span class="row">🆔 ${b.id}</span>
          <span class="row">🎫 ${b.tier}</span>
          <span class="row">🔢 Qty ${b.qty}</span>
          <span class="row">💳 ${money(b.total)}</span>
        </div>
        <span class="status-pill ${b.status}">${icon} ${statusLabel}</span>
      </div>
      <div class="booking-actions">
        <div class="qr-box" title="QR placeholder">▦▦▦</div>
        ${b.status === "pending" ? `<button class="btn btn-success btn-sm" data-paynow="${b.orderId}">Pay Now</button>` : ""}
        <button class="btn btn-outline btn-sm" data-download="${b.id}">Download ticket</button>
        ${b.status !== "cancelled" && b.when === "upcoming" ? `<button class="btn btn-danger-outline btn-sm" data-cancel="${b.id}">Cancel booking</button>` : ""}
      </div>
    </div>`;
  }

  function renderBookings() {
    const upcomingEl = $("#upcomingBookings");
    const previousEl = $("#previousBookings");
    if (!upcomingEl || !previousEl) return;
    const upcoming = state.bookings.filter((b) => b.when === "upcoming");
    const previous = state.bookings.filter((b) => b.when === "previous");
    upcomingEl.innerHTML = upcoming.length ? upcoming.map(bookingCardHTML).join("") : `<div class="empty-state"><div class="icon-wrap">📭</div><h3>No upcoming bookings</h3><p>Browse events to book your next experience.</p><a class="btn btn-primary" href="#" data-goto="browse">Browse events</a></div>`;
    previousEl.innerHTML = previous.length ? previous.map(bookingCardHTML).join("") : `<div class="empty-state"><div class="icon-wrap">🗂️</div><h3>No past bookings yet</h3><p>Your booking history will show up here.</p></div>`;

    $$("[data-cancel]").forEach((btn) => btn.addEventListener("click", () => {
      const b = state.bookings.find((x) => x.id === btn.dataset.cancel);
      if (b) { b.status = "cancelled"; toast("Booking cancelled", `${b.id} has been cancelled.`, "warn"); renderBookings(); }
    }));
    $$("[data-paynow]").forEach((btn) => btn.addEventListener("click", () => payNowFromBookings(btn)));
    $$("[data-download]").forEach((btn) => btn.addEventListener("click", () => {
      toast("Preparing ticket", "Your PDF ticket download will start shortly.", "ok");
    }));
  }

  /* ---------------------------- Home reviews (site-wide) -------------------- */
  function renderHomeReviews() {
    const el = $("#homeReviewsGrid");
    if (!el) return;
    el.innerHTML = MOCK_HOME_REVIEWS.map((r) => `
      <div class="home-review-card">
        <div class="hr-stars">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</div>
        <p class="hr-text">${escapeHTML(r.text)}</p>
        <div class="hr-person">
          <img src="${r.avatar}" alt="">
          <div><div class="hr-name">${escapeHTML(r.name)}</div><div class="hr-event">${escapeHTML(r.event)}</div></div>
        </div>
      </div>`).join("");
  }

  /* ------------------------------- Notifications ----------------------------- */
  const NOTIF_ICON = { confirmed: ["✓", "#DCFCE7", "#067647"], payment: ["💳", "#DBEAFE", "#1D4ED8"], reminder: ["⏰", "#FEF3C7", "#92400E"], updated: ["✎", "#E0F2FE", "#0369A1"], cancelled: ["✕", "#FEE2E2", "#B91C1C"], refund: ["↩", "#EDE9FE", "#6D28D9"] };
  function renderNotifications() {
    const list = $("#notifList");
    if (!list) return;
    if (!MOCK_NOTIFICATIONS.length) {
      list.innerHTML = `<div class="empty-state"><div class="icon-wrap">🔔</div><h3>No notifications</h3><p>You're all caught up.</p></div>`;
      updateNotifBadge();
      return;
    }
    list.innerHTML = MOCK_NOTIFICATIONS.map((n, idx) => {
      const [icon, bg, fg] = NOTIF_ICON[n.type] || ["🔔", "#EEF2F7", "#334155"];
      return `
    <div class="notif-item ${n.unread ? "unread" : ""}" data-idx="${idx}">
      <div class="notif-icon" style="background:${bg};color:${fg}">${icon}</div>
      <div class="notif-body"><strong>${escapeHTML(n.title)}</strong><p>${escapeHTML(n.body)}</p></div>
      <span class="notif-time">${n.time}</span>
      <button type="button" class="notif-delete" data-delete="${idx}" aria-label="Delete notification">✕</button>
    </div>`;
    }).join("");
    updateNotifBadge();
    $$(".notif-item", list).forEach((item) => item.addEventListener("click", (e) => {
      if (e.target.closest("[data-delete]")) return;
      const n = MOCK_NOTIFICATIONS[parseInt(item.dataset.idx, 10)];
      if (n && n.unread) { n.unread = false; renderNotifications(); }
    }));
    $$("[data-delete]", list).forEach((btn) => btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.delete, 10);
      MOCK_NOTIFICATIONS.splice(idx, 1);
      renderNotifications();
    }));
  }
  function updateNotifBadge() {
    const unread = MOCK_NOTIFICATIONS.filter((n) => n.unread).length;
    const badge = $("#notifCount");
    if (badge) {
      badge.textContent = String(unread);
      badge.classList.toggle("hidden", unread === 0);
    }
    const dot = $("#notifDot");
    if (dot) dot.style.display = unread === 0 ? "none" : "block";
  }

  /* --------------------------------- Profile form ----------------------------- */
  function initProfileForm() {
    const form = $("#profileForm");
    if (!form) return;
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      let valid = true;
      $$(".form-field", form).forEach((field) => {
        const input = field.querySelector("input");
        if (!input) return;
        field.classList.remove("invalid");
        if (input.hasAttribute("required") && !input.value.trim()) { field.classList.add("invalid"); valid = false; }
        if (input.type === "email" && input.value && !/^\S+@\S+\.\S+$/.test(input.value)) { field.classList.add("invalid"); valid = false; }
      });
      if (!valid) { toast("Check the form", "Some fields need your attention.", "err"); return; }
      toast("Profile updated", "Your changes have been saved.", "ok");
    });

    $("#avatarUpload")?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => { $("#profileAvatarImg").src = reader.result; };
      reader.readAsDataURL(file);
    });

    const pwdForm = $("#passwordForm");
    pwdForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const next = $("#newPassword");
      const confirm = $("#confirmPassword");
      const field = confirm.closest(".form-field");
      field.classList.remove("invalid");
      if (next.value.length < 8) { next.closest(".form-field").classList.add("invalid"); toast("Weak password", "Use at least 8 characters.", "err"); return; }
      if (next.value !== confirm.value) { field.classList.add("invalid"); toast("Passwords don't match", "Please re-enter to confirm.", "err"); return; }
      toast("Password changed", "Use your new password next time you log in.", "ok");
      pwdForm.reset();
    });
  }

  /* ---------------------------- Newsletter form -------------------------------- */
  function initNewsletter() {
    $("#newsletterForm")?.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = $("#newsletterEmail");
      if (!input.value || !/^\S+@\S+\.\S+$/.test(input.value)) { toast("Invalid email", "Please enter a valid email address.", "err"); return; }
      toast("Subscribed", "You're on the list for event updates.", "ok");
      input.value = "";
    });
  }

  /* --------------------------------- Fraud demo -------------------------------- */
  function initFraud() {
    $("#contactSupportBtn")?.addEventListener("click", () => {
      toast("Support ticket opened", "Our fraud response team will reach out shortly.", "ok");
    });
  }

  /* ---------------------------------- Logout ------------------------------------ */
  function initLogout() {
    $("#logoutBtn")?.addEventListener("click", () => {
      localStorage.removeItem("access_token");
      window.location.href = "../login_sign_in/login.html";
    });
  }

  /* ---------------------------------- Init ------------------------------------- */
  async function init() {
    if (!localStorage.getItem("access_token")) {
      // window.location.href = "../login_sign_in/login.html";
      // return;
    }

    try {
      const me = await (await fetch(`${API_BASE}/users/me`, { headers: authHeaders() })).json();
      if (!me.role_selected) {
        window.location.href = "../role/index.html";
        return;
      }
      if (me.role !== "customer") {
        window.location.href = "../dashboard/dashboard.html";
        return;
      }
      state.currentUser = me;
      applyCustomerIdentity(me);
    } catch (err) {
      console.error("Couldn't verify session:", err);
        localStorage.removeItem("access_token");
        window.location.href = "../login_sign_in/login.html";
        return;
    }

    initNavbar();
    initViews();
    initLogout();
    initSearchSuggestions();
    initFilters();
    initModal();
    initPayment();
    initProfileForm();
    initNewsletter();
    initFraud();
    updateNotifBadge();

    try {
      state.events = await api.getEvents();
    } catch (err) {
      console.error("Couldn't load events:", err);
      state.events = [];
      toast("Couldn't reach the server", "Some content may be missing.", "warn");
    }

    try {
      state.bookings = await api.getBookings(state.events);
    } catch (err) {
      console.error("Couldn't load bookings:", err);
      state.bookings = [];
    }

    renderFeatured();
    renderTrending();
    renderUpcoming();
    renderCategories();
    renderCities();
    renderEvents();
    renderWishlist();
    renderBookings();
    renderNotifications();
    renderHomeReviews();
    initCounters();

    $("#globalLoader")?.classList.add("hidden");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
