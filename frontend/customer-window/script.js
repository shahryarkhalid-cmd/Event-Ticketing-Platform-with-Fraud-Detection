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

  // Static icon/color per category name — no longer a source of truth for
  // *counts* (those come from real fetched events, see deriveCategories()
  // below). Any category name not listed here falls back to a default
  // icon/color in deriveCategories() so new backend categories still render.
  const CATEGORY_META = {
    Music: { icon: "🎵", color: "#EEF2FF" },
    Business: { icon: "💼", color: "#ECFDF5" },
    Art: { icon: "🎨", color: "#FFF7ED" },
    Sports: { icon: "🏆", color: "#FEF2F2" },
    Comedy: { icon: "🎤", color: "#F0F9FF" },
    Technology: { icon: "💻", color: "#F5F3FF" },
  };
  const DEFAULT_CATEGORY_META = { icon: "🎟️", color: "#F1F5F9" };

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

  // No longer used anywhere — notifications are now fetched live from
  // GET /notifications (see api.getNotifications / mapNotificationFromBackend
  // below). Left in place rather than deleted, in case it's useful as a reference.
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

  // For multipart/FormData requests (file uploads) — the browser must set
  // its own "Content-Type: multipart/form-data; boundary=..." header, so we
  // deliberately do NOT send one here (unlike authHeaders() above).
  function authHeadersFormData() {
    const token = localStorage.getItem("access_token");
    return { "Authorization": `Bearer ${token}` };
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
    // "starting price" should show the currency of whichever tier that
    // lowest price actually belongs to, not a hardcoded currency.
    const lowestTier = tiers.find(t => t.price === lowestPrice);
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
      address: evt.address || "",
      description: evt.description || "",
      organizer: "", // no organizer name on Event yet — see note below
      banner: evt.banner_url || "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=1200&auto=format&fit=crop",
      price: lowestPrice,
      currency: lowestTier?.currency || tiers[0]?.currency || "USD",
      seatsLeft: totalRemaining,
      trending: false, // not implemented on backend

      // ===== ELABORATED EVENT FIELDS =====
      startDateTime: (evt.start_datetime || "").slice(0, 16),
      endDateTime: (evt.end_datetime || "").slice(0, 16),
      capacity: evt.max_capacity || 0,
      status: evt.status || "published",
      age: evt.age_restriction || "",
      dresscode: evt.dress_code || "",
      parking: evt.parking_available || false,
      food: evt.food_available || false,
      refund: evt.refund_policy || "",
      postalCode: evt.postal_code || "",
      // ====================================

      tiers: tiers.map(t => ({
        id: t.id,
        name: t.category_name,
        price: t.price,
        currency: t.currency,
        remaining: t.total_seats - t.sold_quantity,
        color: TIER_COLORS[t.category_name] || "#6B7280"
      }))
    };
  }

  // Maps the backend's `payment_status` (or `status`) onto the four states
  // the UI actually knows how to render: "pending", "confirmed", "expired",
  // "cancelled". This matters because order_expiry.py flips stale pending
  // orders to payment_status="expired" server-side (via its 20-minute
  // cutoff cron/job) — that's the source of truth for expiry, not just the
  // client-side countdown. Any status string this doesn't recognise falls
  // back to "cancelled" (safest — hides Pay Now / Download rather than
  // risking showing them for an unknown/unexpected state).
  function normalizeOrderStatus(raw) {
    const s = String(raw || "pending").toLowerCase().trim();
    if (s === "pending" || s === "awaiting_payment") return "pending";
    if (s === "expired" || s === "timed_out") return "expired";
    if (["confirmed", "paid", "completed", "success", "successful", "captured"].includes(s)) return "confirmed";
    if (["cancelled", "canceled", "refunded", "failed", "void"].includes(s)) return "cancelled";
    console.warn(`Unrecognized order status "${raw}" — treating as cancelled.`);
    return "cancelled";
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
    // OrderRead has no currency field on the backend — best-effort recovery
    // by matching this order's tier name back to the event's tier list.
    const matchedTier = matchedEvent?.tiers?.find(t => t.name === tierName);
    const currency = matchedTier?.currency || "USD";
    const qty = items.length
      ? items.reduce((s, i) => s + Number(i.quantity ?? i.qty ?? 0), 0)
      : Number(order.quantity ?? order.ticket_quantity ?? 1);

    const total = order.total_amount ?? order.amount ?? order.total_price ?? order.total ?? 0;
    const rawStatus = normalizeOrderStatus(order.status || order.payment_status);


    const eventTitle = matchedEvent?.title || order.event?.name || order.event?.title || order.event_name || "Event";
    const eventBanner = matchedEvent?.banner || order.event?.banner_url
      || "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=1200&auto=format&fit=crop";
    const eventDate = matchedEvent?.date || (order.event?.start_datetime || "").split("T")[0];
    // Needed on the ticket image (date/time/venue) — not previously kept on the
    // mapped booking object, only used transiently for the upcoming/previous split.
    const eventTime = matchedEvent?.time || (order.event?.start_datetime || "").split("T")[1]?.slice(0, 5) || "";
    const eventVenue = matchedEvent?.venue || order.event?.venue || "";

    const when = eventDate && new Date(eventDate) < new Date(new Date().toDateString()) ? "previous" : "upcoming";

    return {
      id: `ORD-${order.id ?? order.order_id ?? ""}`,
      orderId: order.id ?? order.order_id,
      event: { title: eventTitle, banner: eventBanner, date: eventDate, time: eventTime, venue: eventVenue },
      tier: tierName,
      qty,
      total: Number(total) || 0,
      currency,
      status: rawStatus,
      when,
      // Used to work out the 20-minute payment window for pending tickets.
      // Falls back to null when the backend doesn't send it yet — see
      // getTicketExpiryTime() below for the fallback behaviour.
      createdAt: order.created_at || order.createdAt || order.created || null
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

    // ---- Ticket QR + listing endpoints ----
    // Real contract from Order_services.py / qr_service.py (backend files,
    // not touched here):
    //   GET /orders/{order_id}/tickets -> [{ ticket_uid, status, category_name }, ...]
    //     one entry per physical Ticket row for this order (get_order_tickets)
    //   GET /tickets/{ticket_uid}/qr   -> real PNG (StreamingResponse), one per ticket_uid
    getOrderTickets: async (orderId) => {
      const res = await fetch(`${API_BASE}/orders/${orderId}/tickets`, { headers: authHeaders() });
      if (!res.ok) {
        let detail = "";
        try { const body = await res.json(); detail = formatErrorDetail(body.detail); } catch (e) { /* not JSON */ }
        console.error(`GET /orders/${orderId}/tickets → ${res.status}${detail ? `: ${detail}` : ""}`);
        throw new Error(detail || `Couldn't load tickets for this order (${res.status})`);
      }
      const raw = await res.json();
      const list = Array.isArray(raw) ? raw : [];
      return list.map((t) => ({
        ticketUid: t.ticket_uid,
        status: t.status,
        tierName: t.category_name,
      }));
    },
    // One real PNG QR per ticket_uid — no client-side generation, no fake pattern.
    getTicketQrObjectUrl: async (ticketUid) => {
      const res = await fetch(`${API_BASE}/tickets/${encodeURIComponent(ticketUid)}/qr`, { headers: authHeaders() });
      if (!res.ok) throw new Error(`Couldn't load QR code (${res.status})`);
      const blob = await res.blob();
      return URL.createObjectURL(blob);
    },
  };
  const wait = (ms) => new Promise((res) => setTimeout(res, ms));

  /* ------------------------------- State ---------------------------------- */
  const state = {
    currentUser: null,
    events: [],
    bookings: [],
    notifications: [],
    filters: { q: "", category: "all", country: "all", city: "", dateFrom: "", dateTo: "", price: "all", time: "all", sort: "popular" },
    page: 1,
    perPage: 6,
    wishlist: new Set(["EVT-1003"]),
    activeModalEvent: null,
    cart: {}, // { tierName: qty } for the event currently open in the quick ticket modal
  };

  // Ticket tiers carry their own currency code (organizer picks PKR/USD/AED
  // per tier in the dashboard) — this was previously ignored entirely and
  // every price was hardcoded with a "$" prefix regardless of what the
  // organizer actually set. Now formats using the tier/event's real currency.
  const CURRENCY_PREFIX = { USD: "$", PKR: "PKR ", AED: "AED ", EUR: "€", GBP: "£" };
  const money = (n, curr) => {
    const code = (curr || "USD").toUpperCase();
    const prefix = CURRENCY_PREFIX[code] || `${code} `;
    return prefix + Number(n || 0).toFixed(2);
  };
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

    // Only overwrite if the backend actually sent a value — otherwise leave
    // the form's existing placeholder text alone.
    const phoneInput = $("#phoneField");
    if (phoneInput && user.phone) phoneInput.value = user.phone;

    const cityInput = $("#cityField");
    if (cityInput && user.city) cityInput.value = user.city;

    if (user.profile_picture_url) {
      const avatarImg = $("#profileAvatarImg");
      if (avatarImg) avatarImg.src = user.profile_picture_url;
      // Header avatar (top-right circle next to the notification bell) —
      // has no id in the markup, so it's targeted via its existing class.
      const headerAvatarImg = $(".avatar-btn img");
      if (headerAvatarImg) headerAvatarImg.src = user.profile_picture_url;
    }
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
  function showView(name) {
    $$(".view").forEach((v) => v.classList.toggle("hidden", v.dataset.view !== name));
    $$(".nav-link[data-view]").forEach((l) => l.classList.toggle("active", l.dataset.view === name));
    $$(".bottom-tab[data-view]").forEach((t) => t.classList.toggle("active", t.dataset.view === name));
    window.scrollTo({ top: 0, behavior: "smooth" });
    const active = document.querySelector(`.view[data-view="${name}"]`);
    active?.classList.remove("page-view");
    void active?.offsetWidth; // restart animation
    active?.classList.add("page-view");
  }

  function initViews() {
    const navLinks = $$(".nav-link[data-view]");
    const bottomTabs = $$(".bottom-tab[data-view]");

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

    // Delegated (not per-element) so this also works for [data-goto]
    // elements that get rendered later from backend data — category tiles,
    // city tiles, event cards, etc. — not just what's in the DOM at init.
    document.addEventListener("click", (e) => {
      const el = e.target.closest("[data-goto]");
      if (!el) return;
      e.preventDefault();
      showView(el.dataset.goto);
    });

    // Lets other pages deep-link straight into a specific view — used by
    // payment-result.html so "Go to My Orders" / "Download Your Ticket"
    // after a successful payment lands directly on My Bookings
    // (../customer-window/index.html?view=bookings) instead of Home, where
    // the just-confirmed order's real Download ticket button lives.
    const availableViews = $$(".view[data-view]").map((v) => v.dataset.view);
    const requestedView = new URLSearchParams(window.location.search).get("view");
    showView(availableViews.includes(requestedView) ? requestedView : "home");
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
        <div class="event-card-price">${money(ev.price, ev.currency)}<small>starting price</small></div>
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

  // Groups the real fetched events by their `category` field and counts
  // them — this is what makes the "Browse by category" tiles reflect
  // actual backend data instead of the old hardcoded counts.
  function deriveCategories(events) {
    const counts = {};
    events.forEach((ev) => {
      if (!ev.category) return;
      counts[ev.category] = (counts[ev.category] || 0) + 1;
    });
    return Object.keys(counts).map((name) => {
      const meta = CATEGORY_META[name] || DEFAULT_CATEGORY_META;
      return { name, count: counts[name], icon: meta.icon, color: meta.color };
    }).sort((a, b) => b.count - a.count);
  }

  function renderCategories() {
    const el = $("#categoriesGrid");
    if (!el) return;
    const categories = deriveCategories(state.events);
    if (!categories.length) { el.innerHTML = ""; return; }
    el.innerHTML = categories.map((c) => `
      <a class="cat-tile" href="#" data-goto="browse" data-cat-jump="${c.name}">
        <div class="cat-icon" style="background:${c.color}">${c.icon}</div>
        <span>${c.name}</span>
        <small>${c.count} event${c.count === 1 ? "" : "s"}</small>
      </a>`).join("");
    el.querySelectorAll("[data-cat-jump]").forEach((tile) => {
      tile.addEventListener("click", () => {
        state.filters.category = tile.dataset.catJump;
        state.page = 1;
        const sel = $("#filterCategory");
        if (sel) sel.value = tile.dataset.catJump;
        $$(".tab-chip[data-cat]").forEach((c) => c.classList.toggle("active", c.dataset.cat === tile.dataset.catJump));
        renderEvents();
      });
    });
  }

  function renderCities() {
    const el = $("#citiesGrid");
    if (!el) return;
    el.innerHTML = CITIES.map((c) => `
      <a class="city-tile" href="#" data-goto="browse" data-city-jump="${c.name}">
        <img src="${c.img}" alt="${c.name}" loading="lazy">
        <div class="city-tile-label"><strong>${c.name}</strong></div>
      </a>`).join("");
    el.querySelectorAll("[data-city-jump]").forEach((tile) => {
      tile.addEventListener("click", () => {
        state.filters.city = tile.dataset.cityJump;
        state.page = 1;
        const sel = $("#filterCity");
        if (sel) sel.value = tile.dataset.cityJump;
        renderEvents();
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
    const locationStr = [ev.venue, ev.address, ev.city, ev.country].filter(Boolean).join(", ");
    $("#modalEventDate").textContent = `${dateFmt} · ${ev.time} · ${locationStr}`;
    $("#modalEventDesc").textContent = ev.description || `Join ${ev.organizer} for ${ev.title} in ${ev.city}. Mix and match ticket classes and quantities into a single order below.`;
    // ===== POPULATE ELABORATED EVENT INFO =====
    const infoEl = $("#eventDetailInfo");
    if (infoEl) {
      // Toggle functionality
      const toggleBtn = $("#eventDetailToggle");
      const body = $("#eventDetailBody");
      if (toggleBtn && body) {
        toggleBtn.setAttribute("aria-expanded", "false");
        body.classList.remove("open");
        toggleBtn.onclick = () => {
          const isOpen = body.classList.toggle("open");
          toggleBtn.setAttribute("aria-expanded", String(isOpen));
        };
      }

      $("#infoEventId").textContent = "#" + ev.id;
      $("#infoCategory").textContent = ev.category || "General";
      $("#infoStatus").textContent = (ev.status || "upcoming").replace(/^./, c => c.toUpperCase());
      $("#infoOrganizer").textContent = ev.organizer || "Tixora Events";

      $("#infoVenue").textContent = ev.venue || "—";
      $("#infoAddress").textContent = ev.address || "Not specified";
      $("#infoCity").textContent = ev.city || "—";
      $("#infoCountry").textContent = ev.country || "—";
      $("#infoPostal").textContent = ev.postalCode || "—";

      const fmtDT = (dt) => {
        if (!dt) return "—";
        const d = new Date(dt);
        return isNaN(d) ? dt : d.toLocaleString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
      };
      $("#infoStart").textContent = fmtDT(ev.startDateTime);
      $("#infoEnd").textContent = fmtDT(ev.endDateTime);

      const calcDuration = (start, end) => {
        if (!start || !end) return "—";
        const s = new Date(start), e = new Date(end);
        if (isNaN(s) || isNaN(e)) return "—";
        const diffMs = e - s;
        const hrs = Math.floor(diffMs / 3600000);
        const mins = Math.round((diffMs % 3600000) / 60000);
        if (hrs <= 0 && mins <= 0) return "—";
        return `${hrs > 0 ? hrs + " hr" + (hrs > 1 ? "s" : "") + " " : ""}${mins > 0 ? mins + " min" : ""}`.trim();
      };
      $("#infoDuration").textContent = calcDuration(ev.startDateTime, ev.endDateTime);

      $("#infoCapacity").textContent = (ev.capacity || 0) + " seats";
      $("#infoSeatsLeft").textContent = (ev.seatsLeft ?? 0) + " seats left";

      // Policies as styled tags
      const ageEl = $("#infoAge");
      ageEl.textContent = ev.age ? ev.age + "+" : "All ages welcome";
      ageEl.className = "info-tag" + (ev.age ? "" : " positive");

      const dressEl = $("#infoDress");
      dressEl.textContent = ev.dresscode || "Casual";
      dressEl.className = "info-tag";

      const parkEl = $("#infoParking");
      if (ev.parking === true) {
        parkEl.textContent = "✅ Parking available";
        parkEl.className = "info-tag positive";
      } else if (ev.parking === false) {
        parkEl.textContent = "❌ No parking";
        parkEl.className = "info-tag negative";
      } else {
        parkEl.textContent = "Parking info unavailable";
        parkEl.className = "info-tag";
      }

      const foodEl = $("#infoFood");
      if (ev.food === true) {
        foodEl.textContent = "✅ Food available";
        foodEl.className = "info-tag positive";
      } else if (ev.food === false) {
        foodEl.textContent = "❌ No food";
        foodEl.className = "info-tag negative";
      } else {
        foodEl.textContent = "Food info unavailable";
        foodEl.className = "info-tag";
      }

      const refundEl = $("#infoRefund");
      if (ev.refund && ev.refund.toLowerCase().includes("refund")) {
        refundEl.textContent = ev.refund;
        refundEl.className = "info-tag positive";
      } else if (ev.refund) {
        refundEl.textContent = ev.refund;
        refundEl.className = "info-tag negative";
      } else {
        refundEl.textContent = "No refund policy";
        refundEl.className = "info-tag negative";
      }
    }
    // ==========================================
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
          <span class="class-price">${money(tier.price, tier.currency)}</span>
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
        <span class="ci-right">${money(t.price * t.qty, t.currency)}<button type="button" class="ci-remove" data-remove="${t.id}" aria-label="Remove ${t.name}">✕</button></span>
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
    // No service/convenience fee is charged — total is just the subtotal.
    const fees = 0;
    const total = +(subtotal + fees).toFixed(2);
    // All tiers on one event are assumed to share one currency (organizer
    // side already treats it that way) — fall back to the event's currency
    // when the cart is empty.
    const curr = entries[0]?.currency || ev.currency;

    $("#sumSubtotal").textContent = money(subtotal, curr);
    $("#sumQty").textContent = String(totalQty);
    $("#sumTotal").textContent = money(total, curr);
    // Keep the raw numeric total (and its currency) around so the checkout
    // handler doesn't have to scrape/parse the formatted "PKR 1,234.00"
    // string back out of the DOM.
    state.cartTotal = total;
    state.cartCurrency = curr;

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
          // Use the raw numeric total kept in state instead of scraping the
          // formatted summary text — that used to assume a literal "$"
          // prefix and silently produced NaN for any other currency (PKR,
          // AED, etc).
          total: state.cartTotal,
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
    const paySummaryLocation = [ev.venue, ev.address, ev.city, ev.country].filter(Boolean).join(", ");
    $("#paySummaryMeta").textContent = `${new Date(ev.date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })} · ${paySummaryLocation}`;
    const totalQty = items.reduce((s, i) => s + i.qty, 0);
    $("#paySummaryQty").textContent = String(totalQty);
    $("#paySummaryTotal").textContent = totalStr;
    $("#paySummaryOrderId").textContent = orderId;
    $("#paySummaryItems").innerHTML = items.map((i) => `
      <div class="price-row"><span>${escapeHTML(i.name)} × ${i.qty}</span><span>${money(i.price * i.qty, i.currency)}</span></div>`).join("");
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

  /* --------------------------- Ticket image / QR download --------------------------- */
  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(`Couldn't load image: ${src}`));
      img.src = src;
    });
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // Builds the shared summary rows (event/date/venue/booking) shown once,
  // above the per-ticket QR blocks. Pure display formatting — no data
  // invented here, all values come straight off the mapped booking.
  function buildBookingSummaryLines(booking) {
    const dateFmt = booking.event.date
      ? new Date(booking.event.date + "T00:00:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" })
      : "—";
    return [
      ["Date & time", [dateFmt, booking.event.time].filter(Boolean).join(" · ") || "—"],
      ["Venue", booking.event.venue || "—"],
      ["Booking ID", booking.id],
    ];
  }

  // Renders ONE downloadable ticket image (JPEG) for a SINGLE physical
  // ticket: blue header with the real Tixora logo, event summary, then ONE
  // QR box for this one ticket_uid. Called once per real ticket — for a
  // 10-ticket order this runs 10 times, each with a different real QR, and
  // every other line (event/date/venue/booking id) staying identical.
  // Header blue = var(--primary) #001F54 from styles.css, accent stripe =
  // var(--accent) #4CC9F0 — same brand colors as the rest of the app.
  async function buildTicketCanvas(booking, ticket, index, total, logoImg) {
    const W = 700;
    const HEADER_H = 190;
    const summaryLines = buildBookingSummaryLines(booking);
    const SUMMARY_ROW_H = 26;
    const SUMMARY_H = 50 + summaryLines.length * SUMMARY_ROW_H + 30;
    const QR_SIZE = 240;
    const QR_SECTION_H = QR_SIZE + 110;
    const FOOTER_H = 56;
    const H = HEADER_H + SUMMARY_H + QR_SECTION_H + FOOTER_H;

    const canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, W, H);

    // ---- Blue header with the real logo ----
    ctx.fillStyle = "#001F54";
    ctx.fillRect(0, 0, W, HEADER_H);
    ctx.fillStyle = "#4CC9F0";
    ctx.fillRect(0, HEADER_H - 5, W, 5);

    const logoSize = 64;
    if (logoImg) ctx.drawImage(logoImg, (W - logoSize) / 2, 30, logoSize, logoSize);
    ctx.textAlign = "center";
    ctx.fillStyle = "#FFFFFF";
    ctx.font = "700 26px Arial, sans-serif";
    ctx.fillText("Tixora", W / 2, 30 + logoSize + 30);
    ctx.font = "500 13px Arial, sans-serif";
    ctx.fillStyle = "#B9D3F5";
    ctx.fillText("Secure Event Ticketing · E-Ticket", W / 2, 30 + logoSize + 52);
    ctx.textAlign = "left";

    // ---- Event summary — identical on every ticket in this order ----
    let cy = HEADER_H + 44;
    ctx.fillStyle = "#0F172A";
    ctx.font = "700 22px Arial, sans-serif";
    ctx.fillText(booking.event.title || "Event", 40, cy);
    cy += 30;
    ctx.font = "600 13px Arial, sans-serif";
    const tierLabel = total > 1 ? `${ticket.tierName || booking.tier} · Ticket ${index + 1} of ${total}` : (ticket.tierName || booking.tier);
    const pillW = ctx.measureText(tierLabel).width + 28;
    ctx.fillStyle = "#EEF2FF";
    roundRect(ctx, 40, cy - 18, pillW, 28, 14);
    ctx.fill();
    ctx.fillStyle = "#0B5ED7";
    ctx.fillText(tierLabel, 40 + 14, cy + 1);
    cy += 40;

    summaryLines.forEach(([label, value]) => {
      ctx.font = "400 13px Arial, sans-serif";
      ctx.fillStyle = "#64748B";
      ctx.fillText(label, 40, cy);
      ctx.font = "600 13px Arial, sans-serif";
      ctx.fillStyle = "#0F172A";
      ctx.textAlign = "right";
      ctx.fillText(value, W - 40, cy);
      ctx.textAlign = "left";
      cy += SUMMARY_ROW_H;
    });

    // ---- This ticket's own QR — different on every ticket in the order ----
    const qrTop = HEADER_H + SUMMARY_H + 30;
    const qrX = (W - QR_SIZE) / 2;
    ctx.fillStyle = "#F8FAFC";
    ctx.strokeStyle = "#E2E8F0";
    ctx.lineWidth = 1;
    roundRect(ctx, qrX - 18, qrTop - 18, QR_SIZE + 36, QR_SIZE + 36, 16);
    ctx.fill();
    ctx.stroke();

    if (ticket.qrImg) {
      ctx.drawImage(ticket.qrImg, qrX, qrTop, QR_SIZE, QR_SIZE);
    } else {
      ctx.fillStyle = "#F1F5F9";
      ctx.fillRect(qrX, qrTop, QR_SIZE, QR_SIZE);
      ctx.fillStyle = "#94A3B8";
      ctx.font = "13px Arial, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("QR unavailable", qrX + QR_SIZE / 2, qrTop + QR_SIZE / 2);
      ctx.textAlign = "left";
    }

    ctx.textAlign = "center";
    ctx.font = "500 12px Arial, sans-serif";
    ctx.fillStyle = "#64748B";
    ctx.fillText("Scan this code at entry", W / 2, qrTop + QR_SIZE + 30);
    ctx.font = "400 10px Arial, sans-serif";
    ctx.fillStyle = "#94A3B8";
    ctx.fillText(String(ticket.ticketUid).slice(0, 24), W / 2, qrTop + QR_SIZE + 46);
    ctx.textAlign = "left";

    // ---- Footer ----
    const footerTop = H - FOOTER_H;
    ctx.strokeStyle = "#E2E8F0";
    ctx.beginPath();
    ctx.moveTo(30, footerTop);
    ctx.lineTo(W - 30, footerTop);
    ctx.stroke();
    ctx.textAlign = "center";
    ctx.font = "400 11px Arial, sans-serif";
    ctx.fillStyle = "#94A3B8";
    ctx.fillText("Powered by Tixora — AI-powered fraud protection.", W / 2, footerTop + 28);
    ctx.textAlign = "left";

    return canvas;
  }

  // Downloads N separate JPG files for an N-ticket order — one file per real
  // physical ticket, each with its own real QR from the backend and a unique
  // filename, everything else on the ticket identical. A 10-ticket order
  // produces 10 files, never one combined image with 10 codes on it.
  async function downloadTicketImage(booking, btn) {
    const originalLabel = btn ? btn.textContent : null;
    if (btn) { btn.disabled = true; btn.textContent = "Preparing…"; }
    toast("Preparing tickets", "Fetching your QR code(s) and building your ticket images…", "ok");

    const objectUrlsToRevoke = [];
    try {
      const orderId = booking.orderId ?? String(booking.id).replace(/^ORD-/, "");
      const tickets = await api.getOrderTickets(orderId);
      if (!tickets.length) throw new Error("No tickets found for this booking yet.");

      // Real PNG QR per real ticket_uid — exactly as many QR codes as
      // physical tickets returned by the backend, never more, never faked.
      for (const t of tickets) {
        try {
          const qrUrl = await api.getTicketQrObjectUrl(t.ticketUid);
          objectUrlsToRevoke.push(qrUrl);
          t.qrImg = await loadImage(qrUrl);
        } catch (qrErr) {
          console.error(`Couldn't load QR for ${t.ticketUid}:`, qrErr);
          t.qrImg = null;
        }
      }

      const logoImg = await loadImage("assets/logo-white.png").catch(() => null);
      const total = tickets.length;

      for (let i = 0; i < total; i++) {
        const canvas = await buildTicketCanvas(booking, tickets[i], i, total, logoImg);
        const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.95));
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = total > 1 ? `Tixora-Ticket-${booking.id}-${i + 1}-of-${total}.jpg` : `Tixora-Ticket-${booking.id}.jpg`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
        // Small gap between downloads — some browsers silently drop rapid-fire
        // programmatic downloads if they all fire in the same tick.
        if (i < total - 1) await wait(350);
      }

      toast("Tickets ready", total > 1 ? `${total} ticket images have downloaded.` : "Your ticket image has downloaded.", "ok");
    } catch (err) {
      console.error("Ticket download failed:", err);
      toast("Couldn't prepare ticket", err.message || "Something went wrong. Please try again.", "err");
    } finally {
      objectUrlsToRevoke.forEach((u) => URL.revokeObjectURL(u));
      if (btn) { btn.disabled = false; btn.textContent = originalLabel; }
    }
  }

  /* -------------------------------- Bookings -------------------------------- */
  // Pending tickets have a 20-minute window to be paid for before they expire.
  const TICKET_EXPIRY_MINUTES = 20;
  const TICKET_EXPIRY_MS = TICKET_EXPIRY_MINUTES * 60 * 1000;

  // Turns whatever the backend sent for "created at" into a trustworthy
  // milliseconds-since-epoch value, or null if it can't be trusted.
  // Guards against the two things that were causing tickets to look expired
  // the instant they were booked:
  //   1) the value being unix SECONDS rather than milliseconds (which
  //      `new Date(x)` would otherwise read as sometime in 1970), and
  //   2) a timestamp that, once parsed, lands in the future or more than a
  //      day in the past for a booking the customer is looking at right
  //      now — a sign the format didn't parse the way we expected.
  function parseCreatedAt(raw) {
    if (raw === null || raw === undefined || raw === "") return null;
    let ms = null;
    if (typeof raw === "number") {
      ms = raw < 1e12 ? raw * 1000 : raw; // seconds → ms
    } else if (typeof raw === "string") {
      let str = raw.trim();
      // Many backends (FastAPI/Python included) emit "naive" ISO timestamps
      // with no timezone info at all, e.g. "2026-08-05T11:00:00.123456" —
      // meaning UTC, but with nothing on the string saying so. `new Date()`
      // treats a string like that as LOCAL time, not UTC. For anyone ahead
      // of UTC (Lahore is UTC+5) that silently shifts "createdAt" hours into
      // the past, which pushed the 20-minute expiry into the past too and
      // made the Pay Now button disappear within seconds of booking instead
      // of after 20 minutes. Fix: if there's no Z / +HH:MM / -HH:MM offset,
      // assume UTC and say so explicitly before parsing.
      const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(str);
      if (!hasTimezone && /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(str)) {
        str = str.replace(" ", "T") + "Z";
      }
      const parsed = new Date(str).getTime();
      ms = Number.isNaN(parsed) ? null : parsed;
    }
    if (ms == null) return null;
    const now = Date.now();
    const ONE_DAY = 24 * 60 * 60 * 1000;
    if (ms > now + 60 * 1000 || ms < now - ONE_DAY) return null;
    return ms;
  }

  // Works out (and remembers) when the 20-minute countdown for a pending
  // ticket started. Prefers the real order creation time from the backend;
  // if that isn't available/trustworthy, falls back to "the first time this
  // browser saw this pending booking", cached in sessionStorage so the
  // countdown doesn't reset on refresh.
  function getTicketExpiryTime(b) {
    let createdMs = parseCreatedAt(b.createdAt);
    if (createdMs == null) {
      const key = `tixora_ticket_created_${b.id}`;
      const stored = sessionStorage.getItem(key);
      if (stored) {
        createdMs = Number(stored);
      } else {
        createdMs = Date.now();
        try { sessionStorage.setItem(key, String(createdMs)); } catch (e) { /* storage unavailable — countdown still works this session */ }
      }
    }
    return createdMs + TICKET_EXPIRY_MS;
  }

  function formatCountdown(ms) {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    const mm = Math.floor(totalSeconds / 60);
    const ss = totalSeconds % 60;
    return `${mm}:${String(ss).padStart(2, "0")}`;
  }

  function bookingCardHTML(b) {
    // Backend-confirmed expiry (order_expiry.py already flipped
    // payment_status="expired" server-side) is authoritative — no need to
    // wait on the client-side timer for these, they're already over.
    const isBackendExpired = b.status === "expired";
    const isPendingUpcoming = b.status === "pending" && b.when === "upcoming";

    let expiresAt = null;
    let isExpired = isBackendExpired;
    if (isPendingUpcoming) {
      expiresAt = getTicketExpiryTime(b);
      isExpired = Date.now() >= expiresAt;
      // Local 20-minute window ran out client-side before the backend told
      // us — treat it as expired right away so Pay Now disappears instantly
      // instead of waiting on the next fetch from the server.
      if (isExpired) b.status = "expired";
    }

    const showExpiryMsg = isPendingUpcoming || isBackendExpired;

    // "expired" reuses the "Cancelled ✕" pill styling/label (matches how
    // My Bookings should read: a lapsed order simply reads as cancelled),
    // while still getting its own dedicated expiry line below.
    const pillStatus = b.status === "expired" ? "cancelled" : b.status;
    const statusLabel = { confirmed: "Confirmed", pending: "Pending", cancelled: "Cancelled" }[pillStatus] || "Cancelled";
    const icon = { confirmed: "✓", pending: "…", cancelled: "✕" }[pillStatus] || "✕";

    return `
    <div class="booking-card">
      <div class="booking-media"><img src="${b.event.banner}" alt="${escapeHTML(b.event.title)}" loading="lazy"></div>
      <div class="booking-info">
        <h4>${escapeHTML(b.event.title)}</h4>
        <div class="booking-meta">
          <span class="row">🆔 ${b.id}</span>
          <span class="row">🎫 ${b.tier}</span>
          <span class="row">🔢 Qty ${b.qty}</span>
          <span class="row">💳 ${money(b.total, b.currency)}</span>
        </div>
        <span class="status-pill ${pillStatus}" data-status-pill="${b.id}">${icon} ${statusLabel}</span>
      </div>
      <div class="booking-actions">
        <div class="qr-box" title="QR placeholder">▦▦▦</div>
        ${isPendingUpcoming && !isExpired ? `<button class="btn btn-success btn-sm" data-paynow="${b.orderId}" data-booking="${b.id}">Pay Now</button>` : ""}
        ${b.status === "confirmed" ? `<button class="btn btn-outline btn-sm" data-download="${b.id}">Download ticket</button>` : ""}
        ${showExpiryMsg
        ? `<span class="ticket-expiry-msg${isExpired ? " expired" : ""}" data-booking="${b.id}" data-expires-at="${expiresAt ?? ""}">
      ${isExpired
          ? "❌ This booking has expired and been cancelled."
          : `⏳ Expires in <span class="expiry-countdown">${formatCountdown(expiresAt - Date.now())}</span> if payment is not completed.`}
   </span>`
        : ""}
      </div>
    </div>`;
  }

  // Ticks every second so the "Expires in mm:ss" countdown updates live, and
  // flips a ticket to the expired/cancelled state (hiding Pay Now, updating
  // the status pill, showing "has expired") the moment its 20-minute window
  // runs out — without needing a full re-render of the bookings list.
  function tickTicketExpiries() {
    $$(".ticket-expiry-msg[data-expires-at]").forEach((span) => {
      const expiresAt = Number(span.dataset.expiresAt);
      const bookingId = span.dataset.booking;
      const remaining = expiresAt - Date.now();
      if (remaining <= 0) {
        if (!span.classList.contains("expired")) {
          span.classList.add("expired");
          span.textContent = "❌ This booking has expired and been cancelled.";
          const payBtn = document.querySelector(`[data-paynow][data-booking="${bookingId}"]`);
          if (payBtn) payBtn.remove();
          const pill = document.querySelector(`[data-status-pill="${bookingId}"]`);
          if (pill) { pill.className = "status-pill cancelled"; pill.textContent = "✕ Cancelled"; }
          const b = state.bookings.find((x) => x.id === bookingId);
          if (b) b.status = "expired";
        }
      } else {
        const countdownEl = span.querySelector(".expiry-countdown");
        if (countdownEl) countdownEl.textContent = formatCountdown(remaining);
      }
    });
  }
  setInterval(tickTicketExpiries, 1000);

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
      const b = state.bookings.find((x) => x.id === btn.dataset.download);
      if (b) downloadTicketImage(b, btn);
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
  // NOTE on endpoints: GET /notifications, PATCH /notifications/{id}/read,
  // and DELETE /notifications are assumed from Notification_services.py's
  // get_notifications / mark_notification_read / delete_notification
  // functions. Confirm the exact path/method against your router (or
  // /docs) and adjust the three fetch() calls below if they differ —
  // this backend previously returned 404/405 for guessed paths.
  const NOTIF_ICON = { confirmed: ["✓", "#DCFCE7", "#067647"], payment: ["💳", "#DBEAFE", "#1D4ED8"], reminder: ["⏰", "#FEF3C7", "#92400E"], updated: ["✎", "#E0F2FE", "#0369A1"], cancelled: ["✕", "#FEE2E2", "#B91C1C"], refund: ["↩", "#EDE9FE", "#6D28D9"] };

  function timeAgo(dateStr) {
    if (!dateStr) return "";
    const then = new Date(dateStr);
    if (Number.isNaN(then.getTime())) return "";
    const diffMin = Math.floor((Date.now() - then.getTime()) / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return `${Math.floor(diffHr / 24)}d ago`;
  }

  // Backend Notification row -> shape renderNotifications() expects. Field
  // names are read defensively (title/message/body, is_read/read, etc.)
  // since the Notification model itself wasn't shared — mirrors the same
  // defensive approach used for mapBookingFromBackend above.
  function mapNotificationFromBackend(n) {
    return {
      id: n.id,
      type: n.type || n.category || "reminder",
      title: n.title || n.heading || "Notification",
      body: n.body || n.message || n.description || "",
      time: timeAgo(n.created_at || n.createdAt),
      unread: !(n.is_read ?? n.read ?? false),
    };
  }

  Object.assign(api, {
    getNotifications: async () => {
      const res = await fetch(`${API_BASE}/notifications`, { headers: authHeaders() });
      if (!res.ok) {
        console.error(`GET /notifications → ${res.status}`);
        throw new Error(`Couldn't load notifications (${res.status})`);
      }
      const raw = await res.json();
      return Array.isArray(raw) ? raw.map(mapNotificationFromBackend) : [];
    },
    markNotificationRead: async (id) => {
      const res = await fetch(`${API_BASE}/notifications/{notification_id}/read`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (!res.ok) {
        let detail = "";
        try { const body = await res.json(); detail = formatErrorDetail(body.detail); } catch (e) { /* not JSON */ }
        console.error(`PATCH /notifications/{notification_id}/read → ${res.status}${detail ? `: ${detail}` : ""}`);
        throw new Error(detail || `Couldn't mark as read (${res.status})`);
      }
    },
    // Backend only supports clearing ALL notifications for the user at
    // once (delete_notification takes no notification_id) — there is no
    // single-notification delete route, so the UI offers one "clear all"
    // action instead of a per-item delete button.
    clearAllNotifications: async () => {
      const res = await fetch(`${API_BASE}/notifications/delete`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) {
        let detail = "";
        try { const body = await res.json(); detail = formatErrorDetail(body.detail); } catch (e) { /* not JSON */ }
        console.error(`DELETE /notifications → ${res.status}${detail ? `: ${detail}` : ""}`);
        throw new Error(detail || `Couldn't delete notifications (${res.status})`);
      }
    },
  });

  function renderNotifications() {
    const list = $("#notifList");
    if (!list) return;
    if (!state.notifications.length) {
      list.innerHTML = `<div class="empty-state"><div class="icon-wrap">🔔</div><h3>No notifications</h3><p>You're all caught up.</p></div>`;
      updateNotifBadge();
      return;
    }
    list.innerHTML = state.notifications.map((n) => {
      const [icon, bg, fg] = NOTIF_ICON[n.type] || ["🔔", "#EEF2F7", "#334155"];
      return `
      <div class="notif-item ${n.unread ? "unread" : ""}" data-id="${n.id}">
      <div class="notif-icon" style="background:${bg};color:${fg}">${icon}</div>
      <div class="notif-body"><strong>${escapeHTML(n.title)}</strong><p>${escapeHTML(n.body)}</p></div>
    </div>`;
    }).join("");
    updateNotifBadge();
    $$(".notif-item", list).forEach((item) => item.addEventListener("click", async () => {
      const n = state.notifications.find((x) => String(x.id) === item.dataset.id);
      if (!n || !n.unread) return;
      try {
        await api.markNotificationRead(n.id);
        n.unread = false;
        renderNotifications();
      } catch (err) {
        console.error("Mark as read failed:", err);
        toast("Couldn't update notification", err.message || "Something went wrong.", "err");
      }
    }));
  }

  function initNotifications() {
    $("#clearAllNotifBtn")?.addEventListener("click", async () => {
      if (!state.notifications.length) return;
      if (!confirm("If you want to delete all notifications, OK.")) return;
      try {
        await api.clearAllNotifications();
        state.notifications = [];
        renderNotifications();
        toast("Notifications cleared", "All notifications have been deleted.", "ok");
      } catch (err) {
        console.error("Clear all notifications failed:", err);
        toast("Couldn't clear notifications", err.message || "Something went wrong.", "err");
      }
    });
  }

  function updateNotifBadge() {
    const unread = state.notifications.filter((n) => n.unread).length;
    const badge = $("#notifCount");
    if (badge) {
      badge.textContent = String(unread);
      badge.classList.toggle("hidden", unread === 0);
    }
    const dot = $("#notifDot");
    if (dot) dot.style.display = unread === 0 ? "none" : "block";
  }

  /* --------------------------------- Profile form ----------------------------- */
  // Endpoints below matched against main.py's actual route registrations:
  // PATCH /users/me/update, POST /users/me/profile-picture, and
  // POST /users/me/change-password (User_services.py's
  // update_user_profile_service / upload_profile_picture_service /
  // change_password functions).
  function initProfileForm() {
    const form = $("#profileForm");
    if (!form) return;
    form.addEventListener("submit", async (e) => {
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

      const saveBtn = $('button[type="submit"]', form);
      const originalLabel = saveBtn ? saveBtn.textContent : null;
      if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = "Saving…"; }

      try {
        const payload = {
          full_name: $("#fullName")?.value.trim(),
          phone: $("#phoneField")?.value.trim(),
          city: $("#cityField")?.value.trim(),
        };
        const res = await fetch(`${API_BASE}/users/me/update`, {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const detail = formatErrorDetail(data.detail);
          console.error(`PATCH /users/me/update → ${res.status}${detail ? `: ${detail}` : ""}`);
          throw new Error(detail || `Couldn't save changes (${res.status})`);
        }
        // Merge the backend's response into state so name/phone/city/avatar
        // all reflect what was actually persisted, not just what we typed.
        state.currentUser = { ...state.currentUser, ...data };
        applyCustomerIdentity(state.currentUser);
        toast("Profile updated", "Your changes have been saved.", "ok");
      } catch (err) {
        console.error("Profile update failed:", err);
        toast("Couldn't save profile", err.message || "Something went wrong. Please try again.", "err");
      } finally {
        if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = originalLabel; }
      }
    });

    $("#avatarUpload")?.addEventListener("change", async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const avatarImg = $("#profileAvatarImg");
      const previousSrc = avatarImg ? avatarImg.src : null;

      // Instant local preview while the real upload is in flight.
      const reader = new FileReader();
      reader.onload = () => { if (avatarImg) avatarImg.src = reader.result; };
      reader.readAsDataURL(file);

      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/users/me/profile-picture`, {
          method: "POST",
          headers: authHeadersFormData(),
          body: formData,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const detail = formatErrorDetail(data.detail);
          console.error(`POST /users/me/profile-picture → ${res.status}${detail ? `: ${detail}` : ""}`);
          throw new Error(detail || `Couldn't upload photo (${res.status})`);
        }
        const url = data.profile_picture_url;
        if (state.currentUser) state.currentUser.profile_picture_url = url;
        if (avatarImg && url) avatarImg.src = url;
        // Keep the header avatar (next to the notification bell) in sync too.
        const headerAvatarImg = $(".avatar-btn img");
        if (headerAvatarImg && url) headerAvatarImg.src = url;
        toast("Photo updated", "Your profile picture has been saved.", "ok");
      } catch (err) {
        console.error("Avatar upload failed:", err);
        if (avatarImg && previousSrc) avatarImg.src = previousSrc; // roll back the preview
        toast("Couldn't upload photo", err.message || "Something went wrong. Please try again.", "err");
      } finally {
        e.target.value = ""; // allow re-selecting the same file next time
      }
    });

    const pwdForm = $("#passwordForm");
    pwdForm?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const current = $("#currentPassword");
      const next = $("#newPassword");
      const confirm = $("#confirmPassword");
      const field = confirm.closest(".form-field");
      field.classList.remove("invalid");
      if (next.value.length < 8) { next.closest(".form-field").classList.add("invalid"); toast("Weak password", "Use at least 8 characters.", "err"); return; }
      if (next.value !== confirm.value) { field.classList.add("invalid"); toast("Passwords don't match", "Please re-enter to confirm.", "err"); return; }

      const submitBtn = $('button[type="submit"]', pwdForm);
      const originalLabel = submitBtn ? submitBtn.textContent : null;
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Updating…"; }

      try {
        const res = await fetch(`${API_BASE}/users/me/change-password`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            current_password: current.value,
            new_password: next.value,
          }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const detail = formatErrorDetail(data.detail);
          console.error(`POST /users/me/change-password → ${res.status}${detail ? `: ${detail}` : ""}`);
          throw new Error(detail || `Couldn't update password (${res.status})`);
        }
        toast("Password changed", "Use your new password next time you log in.", "ok");
        pwdForm.reset();
      } catch (err) {
        console.error("Password change failed:", err);
        toast("Couldn't update password", err.message || "Current password may be incorrect.", "err");
      } finally {
        if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalLabel; }
      }
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
    const overlay = $("#logoutConfirmModal");

    $("#logoutBtn")?.addEventListener("click", () => {
      overlay.classList.add("open");
      overlay.setAttribute("aria-hidden", "false");
    });

    $("#logoutCancelBtn")?.addEventListener("click", () => {
      overlay.classList.remove("open");
      overlay.setAttribute("aria-hidden", "true");
    });

    overlay?.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.classList.remove("open");
        overlay.setAttribute("aria-hidden", "true");
      }
    });

    $("#logoutConfirmBtn")?.addEventListener("click", () => {
      localStorage.removeItem("access_token");
      window.location.href = "../Homepage/index.html";
    });
  }


  /* ---------------------------------- Init ------------------------------------- */
  async function init() {
    if (!localStorage.getItem("access_token")) {
      window.location.href = "../login_sign_in/login.html";
      return;
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
      window.location.href = "../Homepage/index.html";
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
    initNotifications();
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

    try {
      state.notifications = await api.getNotifications();
    } catch (err) {
      console.error("Couldn't load notifications:", err);
      state.notifications = [];
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
