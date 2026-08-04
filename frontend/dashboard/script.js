/* ==========================================================================
   Tixora Organizer Dashboard — Application Logic
   Architecture note:
   All data operations go through the `api` object below, which talks to the
   Node/Express + PostgreSQL backend at API_BASE. Every method's real endpoint
   is shown in comments so the mapping between backend shape <-> frontend
   shape stays in one place (mapEventFromBackend / buildPublishPayload etc.)
   ========================================================================== */

(() => {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* Helpers                                                              */
  /* ------------------------------------------------------------------ */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const uid = (p = "id") => `${p}_${Math.random().toString(36).slice(2, 9)}`;
  const currency = (n) => `PKR ${Number(n || 0).toLocaleString("en-PK")}`;
  // NOTE: ticket tiers can carry their own currency (PKR/USD/AED — see
  // mapTierFromBackend), but every revenue sum in this file (computeStats,
  // analytics, revenue) just adds raw numbers together and labels the total
  // "PKR" via this function. If organizers actually use multiple currencies,
  // those totals will be wrong. Proper fix needs backend-side conversion to
  // a single reporting currency — flagging here rather than silently
  // pretending this file handles it.

  function formatDate(d) {
    const date = new Date(d);
    if (isNaN(date)) return d;
    return date.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
  }

  // `dt` is the exact organizer-selected value from an <input type="datetime-local">,
  // e.g. "2026-07-19T18:30". Kept as local wall-clock time — never re-derived
  // from the device clock — so what the organizer picked is what gets stored
  // and displayed everywhere.
  function formatDateTime(dt) {
    if (!dt) return "—";
    const date = new Date(dt);
    if (isNaN(date)) return dt;
    return date.toLocaleString("en-US", { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" });
  }

  function toast(message, type = "default") {
    const stack = $("#toastStack");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateY(8px)";
      setTimeout(() => el.remove(), 250);
    }, 2600);
  }

  const TICKET_COLORS = ["#0B5ED7", "#4CC9F0", "#F59E0B", "#10B981", "#8B5CF6", "#EF4444", "#EC4899"];

  // Key under which a locally-cached organizer record may be kept for this
  // session (used only as a fallback if /auth/me can't be reached).
  const AUTH_STORAGE_KEY = "tixora_auth_user";

  function getInitials(name) {
    const parts = (name || "").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "U";
    return parts.slice(0, 2).map(p => p[0].toUpperCase()).join("");
  }

  /* ------------------------------------------------------------------ */
  /* Fallback data (used only if the backend can't be reached)            */
  /* ------------------------------------------------------------------ */
  const store = {
    // Fallback organizer record — only used if GET /auth/me fails (offline,
    // backend down, etc). Real data always comes from the API when available.
    currentUser: {
      full_name: "Sana Malik",
      email: "sana.malik@tixora.com",
      phone: "+92 300 7654321",
      company: "Tixora Events"
    }
  };

  /* ------------------------------------------------------------------ */
  /* API layer                                                            */
  /* ------------------------------------------------------------------ */
  const API_BASE = "http://localhost:8000";

  function authHeaders() {
    const token = localStorage.getItem("access_token");
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }

  // Thin wrapper so every call gets the same error handling instead of
  // silently trying to JSON-parse an error page / 401 response as data.
  async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
      let detail = "";
      try { detail = await res.text(); } catch (e) { /* ignore */ }
      throw new Error(`${options.method || "GET"} ${url} → ${res.status}${detail ? `: ${detail}` : ""}`);
    }
    return res.json();
  }

  // backend event + tiers -> shape the frontend rendering code expects
  function mapEventFromBackend(evt, tiers) {
    return {
      id: String(evt.id),
      name: evt.name,
      category: evt.category,
      description: evt.description,
      venue: evt.venue,
      address: evt.address,
      city: evt.city,
      country: evt.country,
      // Keep the organizer-selected instant intact as ONE value (never split
      // back into separate date/time) — sliced to "YYYY-MM-DDTHH:mm" so it
      // drops straight into an <input type="datetime-local">.
      startDateTime: (evt.start_datetime || "").slice(0, 16),
      endDateTime: (evt.end_datetime || "").slice(0, 16),
      capacity: evt.max_capacity,
      dresscode: evt.dress_code,
      age: evt.age_restriction,
      parking: evt.parking_available,
      food: evt.food_available,
      refund: evt.refund_policy,
      // Event Image Upload feature — the real backend stores this as
      // `banner_url` on the Event model (set via POST /events/:id/banner).
      banner: evt.banner_url || null,
      // TODO: the backend doesn't distinguish draft/published yet, so
      // "Save as Draft" in the UI doesn't actually persist as a draft —
      // it will come back as whatever `evt.status` is (or "published" if
      // the field isn't sent at all). Once the backend adds a real status
      // column, nothing else here needs to change.
      status: evt.status || "published",
      tickets: (tiers || []).map(mapTierFromBackend)
    };
  }

  function mapTierFromBackend(t) {
    return {
      id: String(t.id),
      name: t.category_name,
      price: t.price,
      currency: t.currency,
      totalSeats: t.total_seats,
      sold: t.sold_quantity,
      availableSeats: t.total_seats - t.sold_quantity,
      description: t.description || "",
      benefits: t.benefits_included || "",
      color: "#0B5ED7"
    };
  }

  // frontend form data -> backend /publish-event payload
  function buildPublishPayload(data) {
    return {
      name: data.name,
      category: data.category,
      description: data.description,
      venue: data.venue,
      address: data.address,
      city: data.city,
      country: data.country,
      // `data.startDateTime` / `data.endDateTime` come straight from the
      // <input type="datetime-local">, e.g. "2026-08-01T19:30" — append
      // seconds for the backend's expected ISO format. This is the organizer's
      // exact selection, never the device clock.
      start_datetime: data.startDateTime ? `${data.startDateTime}:00` : null,
      end_datetime: data.endDateTime ? `${data.endDateTime}:00` : null,
      max_capacity: data.capacity,
      dress_code: data.dresscode,
      age_restriction: data.age ? Number(data.age) : null,
      parking_available: data.parking,
      food_available: data.food,
      refund_policy: data.refund,
      terms_accepted: true,
      // NOTE: the ticket-category editor also collects `color`, `salesStart`,
      // `salesEnd`, and `maxPerPerson` per tier, but the backend's ticket-tier
      // schema (as used elsewhere in this file) has no fields for them, so
      // they are intentionally NOT sent here — sending unknown keys silently
      // to an unfamiliar backend is worse than dropping them loudly. Flag to
      // the backend team if these need to persist.
      ticket_tiers: data.tickets.map(t => ({
        category_name: t.name,
        price: t.price,
        currency: t.currency,
        total_seats: t.totalSeats,
        benefits_included: t.benefits,
        description: t.description
      }))
    };
  }

  function mapBookingFromBackend(b) {
    return {
      customer: b.customer,
      email: b.email,
      eventName: b.event,
      category: b.category,
      qty: b.qty,
      amount: b.amount,
      date: b.date,
      status: b.status,
      qr: b.qr_generated
    };
  }

  function mapNotificationFromBackend(n) {
    return {
      id: n.id,
      title: n.title,
      body: n.body,
      time: formatDateTime(n.created_at),
      isRead: n.is_read,
      type: "sold" // backend has no real `type` field yet — defaulting until it does
    };
  }

  const api = {
    events: {
      // GET /get_all_events (+ GET /events/:id/ticket-tiers per event)
      async list() {
        const rawEvents = await fetchJSON(`${API_BASE}/get_all_events`, { headers: authHeaders() });
        return Promise.all(rawEvents.map(async (evt) => {
          const tiers = await fetchJSON(`${API_BASE}/events/${evt.id}/ticket-tiers`, { headers: authHeaders() });
          return mapEventFromBackend(evt, tiers);
        }));
      },
      // GET /get_event/:id
      async get(id) {
        const evt = await fetchJSON(`${API_BASE}/get_event/${id}`, { headers: authHeaders() });
        const tiers = await fetchJSON(`${API_BASE}/events/${id}/ticket-tiers`, { headers: authHeaders() });
        return mapEventFromBackend(evt, tiers);
      },
      // POST /publish-event
      async create(payload) {
        const data = await fetchJSON(`${API_BASE}/publish-event`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(buildPublishPayload(payload))
        });
        return mapEventFromBackend(data.event, data.ticket_tiers);
      },
      // PUT /update_event/:id
      async update(id, payload) {
        const data = await fetchJSON(`${API_BASE}/update_event/${id}`, {
          method: "PUT",
          headers: authHeaders(),
          body: JSON.stringify(buildPublishPayload(payload))
        });
        return mapEventFromBackend(data.event, data.ticket_tiers);
      },
      // DELETE /delete_event/:id
      async remove(id) {
        return fetchJSON(`${API_BASE}/delete_event/${id}`, { method: "DELETE", headers: authHeaders() });
      },
      // POST /events/:id/banner — multipart file upload (separate from event
      // create/update; the event must already exist since this needs its id).
      async uploadBanner(id, file) {
        const token = localStorage.getItem("access_token");
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/events/${id}/banner`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }, // no Content-Type — browser sets the multipart boundary
          body: formData
        });
        if (!res.ok) {
          let detail = "";
          try { const errBody = await res.json(); detail = errBody.detail; } catch (e) { /* ignore */ }
          console.error(`POST /events/${id}/banner → ${res.status}${detail ? `: ${detail}` : ""}`);
          throw new Error(detail || `Banner upload failed (${res.status})`);
        }
        return res.json(); // { banner_url }
      }
    },
    bookings: {
      // GET /organizer/bookings
      async list() {
        const raw = await fetchJSON(`${API_BASE}/organizer/bookings`, { headers: authHeaders() });
        return raw.map(mapBookingFromBackend);
      }
    },
    notifications: {
      // GET /notifications
      async list() {
        const raw = await fetchJSON(`${API_BASE}/notifications`, { headers: authHeaders() });
        return raw.map(mapNotificationFromBackend);
      },
      // POST /notifications/:id/read
      async markRead(id) {
        return fetchJSON(`${API_BASE}/notifications/${id}/read`, {
          method: "POST",
          headers: authHeaders()
        });
      },
      // DELETE /notifications/delete
      async clearAll() {
        return fetchJSON(`${API_BASE}/notifications/delete`, {
          method: "DELETE",
          headers: authHeaders()
        });
      }
    },
    fraud: {
      // GET /organizer/fraud-orders
      async list() { return fetchJSON(`${API_BASE}/organizer/fraud-orders`, { headers: authHeaders() }); }
    },
    analytics: {
      // GET /organizer/analytics/summary
      async summary() { return fetchJSON(`${API_BASE}/organizer/analytics/summary`, { headers: authHeaders() }); },
      // GET /organizer/analytics/ticket-sales
      async ticketSales() { return fetchJSON(`${API_BASE}/organizer/analytics/ticket-sales`, { headers: authHeaders() }); },
      // GET /organizer/analytics/popular-categories
      async popularCategories() { return fetchJSON(`${API_BASE}/organizer/analytics/popular-categories`, { headers: authHeaders() }); }
    },
    revenue: {
      // GET /organizer/revenue/overview
      async overview() { return fetchJSON(`${API_BASE}/organizer/revenue/overview`, { headers: authHeaders() }); },
      // GET /organizer/revenue/trend
      async trend() { return fetchJSON(`${API_BASE}/organizer/revenue/trend`, { headers: authHeaders() }); }
    },
    auth: {
      // GET /users/me — resolves the authenticated user from the JWT.
      async me() {
        try {
          return await fetchJSON(`${API_BASE}/users/me`, { headers: authHeaders() });
        } catch (err) {
          console.warn("Falling back to local organizer record:", err.message);
          try {
            const raw = localStorage.getItem(AUTH_STORAGE_KEY);
            if (raw) return JSON.parse(raw);
          } catch (e) { /* private mode / no storage — ignore */ }
          return structuredClone(store.currentUser);
        }
      }
    }
  };

  /* ------------------------------------------------------------------ */
  /* App state                                                            */
  /* ------------------------------------------------------------------ */
  let currentUser = null;
  let events = [];
  let bookings = [];
  let notifications = [];
  let fraudRecords = [];
  let currentTicketDraft = []; // ticket categories being edited in the Create/Edit form
  let editingEventId = null;
  let currentBannerFile = null; // the File object to upload via POST /events/:id/banner
  let currentBannerPreviewUrl = null; // data URL used only for the local <img> preview
  let pendingDeleteId = null;

  /* ------------------------------------------------------------------ */
  /* Navigation / routing                                                 */
  /* ------------------------------------------------------------------ */
  const VIEW_META = {
    dashboard: { title: "Dashboard", crumb: "Overview" },
    events: { title: "My Events", crumb: "All Events" },
    create: { title: "Create Event", crumb: "New Event" },
    tickets: { title: "Manage Events", crumb: "Ticket Categories" },
    bookings: { title: "Bookings", crumb: "All Bookings" },
    analytics: { title: "Analytics", crumb: "Performance" },
    revenue: { title: "Revenue", crumb: "Earnings" },
    fraud: { title: "Fraud Detection", crumb: "Risk & Security" },
    notifications: { title: "Notifications", crumb: "Activity" },
    profile: { title: "Profile", crumb: "Organizer" },
    settings: { title: "Settings", crumb: "Preferences" }
  };

  function goTo(view) {
    if (!VIEW_META[view]) view = "dashboard";
    $$(".view").forEach(v => v.classList.remove("active"));
    const target = $(`#view-${view}`);
    if (target) target.classList.add("active");

    $$(".nav-item[data-view]").forEach(n => n.classList.toggle("active", n.dataset.view === view));
    $("#pageTitle").textContent = VIEW_META[view].title;
    $("#breadcrumbCurrent").textContent = VIEW_META[view].crumb;

    if (view === "create" && editingEventId === null) { resetEventForm(); maybeStartCreateTour(); }
    if (view === "tickets") renderTicketEventPicker();
    if (view === "bookings") renderBookingsTable($("#bookingsTable tbody"), bookings);
    if (view === "notifications") renderNotifications($("#notifListFull"), notifications, true);
    if (view === "analytics") renderAnalyticsView();
    if (view === "revenue") renderRevenueView();
    if (view === "fraud") applyFraudFilters();

    closeSidebarMobile();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function closeSidebarMobile() {
    $("#sidebar").classList.remove("open");
    $("#sidebarOverlay").classList.remove("open");
  }

  /* ------------------------------------------------------------------ */
  /* Stats                                                                */
  /* ------------------------------------------------------------------ */
  const STAT_ICONS = {
    events: `<svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7Z"/></svg>`,
    upcoming: `<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>`,
    tickets: `<svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M9 6v4M9 14v4"/></svg>`,
    revenue: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M15 9.5c0-1.4-1.3-2.5-3-2.5s-3 1-3 2.3c0 3 6 1.4 6 4.4 0 1.4-1.3 2.5-3 2.5s-3-1.1-3-2.5"/></svg>`
  };

  function computeStats() {
    const now = new Date();
    const totalEvents = events.length;
    // The backend has no "upcoming"/"live" status (see mapEventFromBackend),
    // so derive it from the event's own start time instead of a status flag
    // that will never actually be set to those values.
    const upcoming = events.filter(e => e.startDateTime && new Date(e.startDateTime) > now).length;
    const ticketsSold = events.reduce((sum, e) => sum + e.tickets.reduce((s, t) => s + (t.sold || 0), 0), 0);
    const revenue = events.reduce((sum, e) => sum + e.tickets.reduce((s, t) => s + (t.sold || 0) * t.price, 0), 0);
    return { totalEvents, upcoming, ticketsSold, revenue };
  }

  function animateCounter(el, target, isCurrency) {
    const duration = 900;
    const start = performance.now();
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const val = Math.round(target * eased);
      el.textContent = isCurrency ? currency(val) : val.toLocaleString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function statCardHTML({ key, label, value, isCurrency, trend, tint, color }) {
    return `
      <div class="stat-card">
        <div class="stat-top">
          <div class="stat-icon" style="background:${tint};color:${color}">${STAT_ICONS[key]}</div>
          <span class="stat-trend ${trend >= 0 ? "up" : "down"}">${trend >= 0 ? "+" : ""}${trend}%</span>
        </div>
        <div class="stat-value" data-count data-target="${value}" data-currency="${!!isCurrency}">${isCurrency ? currency(0) : 0}</div>
        <div class="stat-label">${label}</div>
      </div>`;
  }

  function renderStats(container) {
    const s = computeStats();
    container.innerHTML = [
      statCardHTML({ key: "events", label: "Total Events", value: s.totalEvents, trend: 8, tint: "var(--primary-tint)", color: "var(--primary)" }),
      statCardHTML({ key: "upcoming", label: "Upcoming Events", value: s.upcoming, trend: 4, tint: "var(--secondary-tint)", color: "var(--secondary)" }),
      statCardHTML({ key: "tickets", label: "Tickets Sold", value: s.ticketsSold, trend: 12, tint: "var(--accent-tint)", color: "#0891B2" }),
      statCardHTML({ key: "revenue", label: "Total Revenue", value: s.revenue, isCurrency: true, trend: 16, tint: "var(--success-tint)", color: "var(--success)" })
    ].join("");
    $$("[data-count]", container).forEach(el => {
      animateCounter(el, Number(el.dataset.target), el.dataset.currency === "true");
    });
  }

  /* ------------------------------------------------------------------ */
  /* Events grid rendering                                               */
  /* ------------------------------------------------------------------ */
  function statusBadge(status) {
    const labels = { draft: "Draft", published: "Published", upcoming: "Upcoming", live: "Live", finished: "Finished", cancelled: "Cancelled" };
    return `<span class="badge badge-${status}">${labels[status] || status}</span>`;
  }

  function eventCardHTML(evt) {
    const sold = evt.tickets.reduce((s, t) => s + (t.sold || 0), 0);
    const revenue = evt.tickets.reduce((s, t) => s + (t.sold || 0) * t.price, 0);
    return `
    <article class="event-card" data-id="${evt.id}">
      <div class="event-poster" role="img" aria-label="${evt.name} banner">${evt.banner ? `<img src="${evt.banner}" alt="" loading="lazy" />` : ""}</div>
      <div class="event-body">
        <div class="event-top-row">
          <h4 class="event-name">${evt.name}</h4>
          ${statusBadge(evt.status)}
        </div>
        <p class="event-meta">
          <svg viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
          ${evt.venue}, ${evt.city}
        </p>
        <p class="event-meta">
          <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
          ${formatDateTime(evt.startDateTime)}
        </p>
        <p class="event-meta">
          <svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78Z"/></svg>
          ${evt.category}
        </p>
        <div class="event-stats-row">
          <div><div class="val">${sold}</div><div class="lbl">Tickets Sold</div></div>
          <div><div class="val">${currency(revenue)}</div><div class="lbl">Revenue</div></div>
        </div>
        <div class="event-actions">
          <button data-action="view" title="View"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"/><circle cx="12" cy="12" r="3"/></svg>View</button>
          <button data-action="edit" title="Edit"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>Edit</button>
          <button data-action="duplicate" title="Duplicate"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>Copy</button>
          <button data-action="delete" class="danger" title="Delete"><svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6"/></svg>Delete</button>
        </div>
      </div>
    </article>`;
  }

  function applyEventFilters(list) {
    const q = ($("#eventSearch")?.value || "").toLowerCase().trim();
    const status = $("#filterStatus")?.value || "all";
    const category = $("#filterCategory")?.value || "all";
    const sort = $("#sortBy")?.value || "newest";

    let out = list.filter(e => {
      const matchQ = !q || e.name.toLowerCase().includes(q) || e.city.toLowerCase().includes(q) || e.venue.toLowerCase().includes(q);
      const matchStatus = status === "all" || e.status === status;
      const matchCat = category === "all" || e.category === category;
      return matchQ && matchStatus && matchCat;
    });

    const revenueOf = e => e.tickets.reduce((s, t) => s + (t.sold || 0) * t.price, 0);
    const ticketsOf = e => e.tickets.reduce((s, t) => s + (t.sold || 0), 0);

    if (sort === "newest") out = out.slice().reverse();
    if (sort === "oldest") out = out.slice();
    if (sort === "revenue") out = out.slice().sort((a, b) => revenueOf(b) - revenueOf(a));
    if (sort === "tickets") out = out.slice().sort((a, b) => ticketsOf(b) - ticketsOf(a));

    return out;
  }

  function renderEventsGrid() {
    const filtered = applyEventFilters(events);
    const grid = $("#eventsGrid");
    const gridFull = $("#eventsGridFull");
    const empty = $("#emptyState");
    const emptyFull = $("#emptyStateFull");
    const toolbar = $("#eventsToolbar");
    const toolbar2 = $("#eventsToolbar2");
    const hasEvents = events.length > 0;

    const html = filtered.length
      ? filtered.map(eventCardHTML).join("")
      : `<div class="no-tickets-msg" style="grid-column:1/-1;">No events match your search or filters.</div>`;
    if (grid) grid.innerHTML = html;
    if (gridFull) gridFull.innerHTML = html;

    // No events at all -> hide toolbar + grid, show a professional empty state with CTA
    if (toolbar) toolbar.hidden = !hasEvents;
    if (grid) grid.hidden = !hasEvents;
    if (empty) empty.hidden = hasEvents;

    if (toolbar2) toolbar2.hidden = !hasEvents;
    if (gridFull) gridFull.hidden = !hasEvents;
    if (emptyFull) emptyFull.hidden = hasEvents;

    // populate category filter dynamically
    const catSelect = $("#filterCategory");
    if (catSelect) {
      const cats = [...new Set(events.map(e => e.category))];
      const current = catSelect.value;
      catSelect.innerHTML = `<option value="all">All Categories</option>` + cats.map(c => `<option value="${c}">${c}</option>`).join("");
      catSelect.value = cats.includes(current) ? current : "all";
    }
  }

  function bindEventCardActions(container) {
    container.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-action]");
      if (!btn) return;
      const card = e.target.closest(".event-card");
      const id = card.dataset.id;
      const action = btn.dataset.action;
      const evt = events.find(x => x.id === id);
      if (!evt) return;

      if (action === "view") openViewModal(evt);
      if (action === "edit") openEditForm(evt);
      if (action === "delete") openDeleteModal(evt.id);
      if (action === "duplicate") duplicateEvent(evt);
    });
  }

  async function duplicateEvent(evt) {
    const copy = structuredClone(evt);
    delete copy.id;
    copy.name = `${copy.name} (Copy)`;
    copy.status = "draft"; // NOTE: backend has no draft concept yet — see TODO in mapEventFromBackend
    copy.tickets = copy.tickets.map(t => ({ ...t, id: uid("tkt"), sold: 0, availableSeats: t.totalSeats }));
    try {
      await api.events.create(copy);
      events = await api.events.list();
      refreshAllEventViews();
      toast(`Duplicated "${evt.name}"`, "success");
    } catch (err) {
      console.error(err);
      toast("Couldn't duplicate this event — please try again.", "danger");
    }
  }

  /* ------------------------------------------------------------------ */
  /* View event modal                                                     */
  /* ------------------------------------------------------------------ */
  function openViewModal(evt) {
    const sold = evt.tickets.reduce((s, t) => s + (t.sold || 0), 0);
    const revenue = evt.tickets.reduce((s, t) => s + (t.sold || 0) * t.price, 0);
    $("#viewEventBody").innerHTML = `
      <div class="event-poster" style="height:160px;border-radius:12px;margin-bottom:16px;"></div>
      <h3 style="margin:0 0 4px;">${evt.name}</h3>
      <p style="color:var(--muted);font-size:13.5px;margin:0 0 16px;">${evt.description || "No description provided."}</p>
      <div class="detail-row"><span class="k">Status</span><span class="v">${statusBadge(evt.status)}</span></div>
      <div class="detail-row"><span class="k">Category</span><span class="v">${evt.category}</span></div>
      <div class="detail-row"><span class="k">Venue</span><span class="v">${evt.venue}, ${evt.city}, ${evt.country}</span></div>
      <div class="detail-row"><span class="k">Starts</span><span class="v">${formatDateTime(evt.startDateTime)}</span></div>
      <div class="detail-row"><span class="k">Ends</span><span class="v">${formatDateTime(evt.endDateTime)}</span></div>
      <div class="detail-row"><span class="k">Capacity</span><span class="v">${evt.capacity} seats</span></div>
      <div class="detail-row"><span class="k">Tickets Sold</span><span class="v">${sold}</span></div>
      <div class="detail-row"><span class="k">Revenue</span><span class="v">${currency(revenue)}</span></div>
      <h4 style="margin:18px 0 10px;font-size:14px;">Ticket Categories</h4>
      <div class="ticket-categories">
        ${evt.tickets.map(t => `
          <div class="ticket-card">
            <div class="ticket-card-top">
              <span class="ticket-card-title"><span class="ticket-color-badge" style="background:${t.color}"></span>${t.name}</span>
              <strong>${currency(t.price)}</strong>
            </div>
            <p style="font-size:12.5px;color:var(--muted);margin:0 0 6px;">${t.benefits || "—"}</p>
            <p style="font-size:12.5px;margin:0;">${t.sold}/${t.totalSeats} sold</p>
          </div>`).join("")}
      </div>`;
    openModal("viewEventModal");
  }

  /* ------------------------------------------------------------------ */
  /* Delete modal                                                         */
  /* ------------------------------------------------------------------ */
  function openDeleteModal(id) {
    pendingDeleteId = id;
    openModal("deleteModal");
  }

  /* ------------------------------------------------------------------ */
  /* Modal helpers                                                        */
  /* ------------------------------------------------------------------ */
  function openModal(id) { $(`#${id}`).classList.add("open"); document.body.style.overflow = "hidden"; }
  function closeModal(id) { $(`#${id}`).classList.remove("open"); document.body.style.overflow = ""; }

  /* ------------------------------------------------------------------ */
  /* Ticket category editor (inside Create/Edit event form)               */
  /* ------------------------------------------------------------------ */
  function newTicketCategory() {
    return {
      id: uid("tkt"), name: "", price: 0, currency: "PKR", totalSeats: 0, availableSeats: 0, sold: 0,
      description: "", benefits: "", color: TICKET_COLORS[currentTicketDraft.length % TICKET_COLORS.length],
      salesStart: "", salesEnd: "", maxPerPerson: 4
    };
  }

  function ticketCategoryCardHTML(t, index) {
    return `
    <div class="ticket-card" data-tid="${t.id}">
      <div class="ticket-card-top">
        <span class="ticket-card-title"><span class="ticket-color-badge" style="background:${t.color}"></span>Category ${index + 1}</span>
        <div class="ticket-card-actions">
          <button type="button" data-tk-action="duplicate" title="Duplicate"><svg viewBox="0 0 24 24"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>
          <button type="button" data-tk-action="delete" title="Delete"><svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6"/></svg></button>
        </div>
      </div>
      <div class="ticket-field-row">
        <label>Category Name <input type="text" data-tk="name" value="${t.name}" placeholder="e.g. VIP" /></label>
        <label>Color <input type="color" data-tk="color" value="${t.color}" style="padding:2px;height:34px;" /></label>
      </div>
      <div class="ticket-field-row">
        <label>Price <input type="number" min="0" data-tk="price" value="${t.price}" /></label>
        <label>Currency
          <select data-tk="currency">
            <option ${t.currency === "PKR" ? "selected" : ""}>PKR</option>
            <option ${t.currency === "USD" ? "selected" : ""}>USD</option>
            <option ${t.currency === "AED" ? "selected" : ""}>AED</option>
          </select>
        </label>
      </div>
      <div class="ticket-field-row">
        <label>Total Seats <input type="number" min="0" data-tk="totalSeats" value="${t.totalSeats}" /></label>
        <label>Max Tickets / Person <input type="number" min="1" data-tk="maxPerPerson" value="${t.maxPerPerson}" /></label>
      </div>
      <div class="ticket-field-row">
        <label>Sales Start <input type="date" data-tk="salesStart" value="${t.salesStart}" /></label>
        <label>Sales End <input type="date" data-tk="salesEnd" value="${t.salesEnd}" /></label>
      </div>
      <div class="ticket-field-row full">
        <label>Benefits Included <input type="text" data-tk="benefits" value="${t.benefits}" placeholder="e.g. Front Row, Free Drinks" /></label>
      </div>
      <div class="ticket-field-row full">
        <label>Description <textarea rows="2" data-tk="description" placeholder="Short description">${t.description}</textarea></label>
      </div>
    </div>`;
  }

  function renderTicketDraft() {
    const container = $("#ticketCategories");
    if (currentTicketDraft.length === 0) {
      container.innerHTML = `<div class="no-tickets-msg">No ticket categories yet — click "Add Ticket Category" to create General, VIP, VVIP, or any custom tier.</div>`;
    } else {
      container.innerHTML = currentTicketDraft.map(ticketCategoryCardHTML).join("");
    }
    updateCapacityMeter();
  }

  function updateCapacityMeter() {
    const capacity = Number($("#f_capacity").value) || 0;
    const used = currentTicketDraft.reduce((s, t) => s + (Number(t.totalSeats) || 0), 0);
    const pct = capacity > 0 ? Math.min(100, Math.round((used / capacity) * 100)) : 0;
    $("#capacityUsedLabel").textContent = `${used} / ${capacity || 0} Seats Used`;
    $("#capacityPercentLabel").textContent = `${pct}%`;
    const fill = $("#capacityFill");
    fill.style.width = `${pct}%`;
    fill.classList.toggle("over", capacity > 0 && used > capacity);
  }

  function bindTicketDraftEvents() {
    const container = $("#ticketCategories");
    container.addEventListener("input", (e) => {
      const field = e.target.dataset.tk;
      if (!field) return;
      const card = e.target.closest("[data-tid]");
      const t = currentTicketDraft.find(x => x.id === card.dataset.tid);
      if (!t) return;
      t[field] = e.target.type === "number" ? Number(e.target.value) : e.target.value;
      if (field === "totalSeats") { t.availableSeats = t.totalSeats - (t.sold || 0); updateCapacityMeter(); }
      if (field === "color") card.querySelector(".ticket-color-badge").style.background = t.color;
    });

    container.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-tk-action]");
      if (!btn) return;
      const card = e.target.closest("[data-tid]");
      const idx = currentTicketDraft.findIndex(x => x.id === card.dataset.tid);
      if (btn.dataset.tkAction === "delete") {
        currentTicketDraft.splice(idx, 1);
      } else if (btn.dataset.tkAction === "duplicate") {
        const copy = { ...currentTicketDraft[idx], id: uid("tkt") };
        currentTicketDraft.splice(idx + 1, 0, copy);
      }
      renderTicketDraft();
    });

    $("#f_capacity").addEventListener("input", updateCapacityMeter);
  }

  /* ------------------------------------------------------------------ */
  /* Create / Edit event form                                             */
  /* ------------------------------------------------------------------ */
  function resetEventForm() {
    editingEventId = null;
    currentTicketDraft = [];
    currentBannerFile = null;
    $("#eventForm").reset();
    $("#eventFormTitle").textContent = "Create Event";
    $("#publishBtn").textContent = "Publish Event";
    setBannerPreview(null);
    renderTicketDraft();
  }

  /* ------------------------------------------------------------------ */
  /* Event Image Upload — banner file select, preview, and removal       */
  /* The actual upload happens separately via POST /events/:id/banner    */
  /* (see api.events.uploadBanner) once the event has a real id.         */
  /* ------------------------------------------------------------------ */
  function setBannerPreview(url) {
    currentBannerPreviewUrl = url || null;
    const wrap = $("#bannerPreviewWrap");
    const img = $("#bannerPreviewImg");
    if (currentBannerPreviewUrl) {
      img.src = currentBannerPreviewUrl;
      wrap.style.display = "";
    } else {
      img.src = "";
      wrap.style.display = "none";
    }
  }

  function bindBannerUpload() {
    const input = $("#f_banner");
    const removeBtn = $("#removeBannerBtn");
    if (!input) return;

    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;

      // Mirrors the backend's own validation (Banner_services.py) so the
      // organizer gets instant feedback instead of waiting on a round-trip.
      const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
      if (!ALLOWED_TYPES.includes(file.type)) {
        toast("Please choose a JPEG, PNG, or WEBP image.", "danger");
        input.value = "";
        return;
      }
      const MAX_BYTES = 5 * 1024 * 1024; // backend's MAX_SIZE_MB = 5
      if (file.size > MAX_BYTES) {
        toast("Image is too large — please choose one under 5MB.", "danger");
        input.value = "";
        return;
      }

      currentBannerFile = file;
      const reader = new FileReader();
      reader.onload = () => setBannerPreview(reader.result);
      reader.onerror = () => toast("Couldn't read that image — please try another file.", "danger");
      reader.readAsDataURL(file); // local preview only — the actual upload sends `file` itself
    });

    removeBtn?.addEventListener("click", () => {
      input.value = "";
      currentBannerFile = null;
      setBannerPreview(null);
      // NOTE: this only clears the pending selection client-side. There is
      // no backend endpoint to delete an already-uploaded banner_url, so if
      // the event already has one, it will remain until replaced with a new upload.
    });
  }

  /* ------------------------------------------------------------------ */
  /* First-time "Create Event" onboarding tour (~5-6s, auto-plays once)   */
  /* ------------------------------------------------------------------ */
  const TOUR_SEEN_KEY = "tixora_create_tour_seen";
  const TOUR_STEP_MS = 950;
  const TOUR_STEPS = [
    { target: "#tourBasicInfo", eyebrow: "Step 1", title: "Start with the basics", text: "Give your event a name, pick a category, and describe it for attendees." },
    { target: "#tourVenue", eyebrow: "Step 2", title: "Set the venue", text: "Add where it's happening — venue, address, city and country." },
    { target: "#tourDateTime", eyebrow: "Step 3", title: "Pick date & time", text: "Choose when doors open and when the event wraps up." },
    { target: "#tourCapacity", eyebrow: "Step 4", title: "Set capacity & policies", text: "Cap total seats and add optional details like dress code or refund policy." },
    { target: "#tourTickets", eyebrow: "Step 5", title: "Add ticket categories", text: "Create tiers like General or VIP — each with its own price and seat count." },
    { target: "#publishBtn", eyebrow: "Step 6", title: "Publish when ready", text: "Hit Publish to make it live, or save it as a draft for later." }
  ];

  let tourEls = null;
  let tourTimer = null;

  function buildTourEls() {
    if (tourEls) return tourEls;
    const scrim = document.createElement("div");
    scrim.className = "tour-scrim";
    const highlight = document.createElement("div");
    highlight.className = "tour-highlight";
    const tooltip = document.createElement("div");
    tooltip.className = "tour-tooltip";
    tooltip.innerHTML = `
      <p class="tour-eyebrow"></p>
      <h4></h4>
      <p class="tour-desc"></p>
      <div class="tour-progress"></div>
      <div class="tour-tooltip-foot">
        <span class="tour-stepcount"></span>
        <button type="button" class="tour-skip">Skip tour</button>
      </div>`;
    document.body.append(scrim, highlight, tooltip);
    tourEls = { scrim, highlight, tooltip };
    tooltip.querySelector(".tour-skip").addEventListener("click", endCreateTour);
    return tourEls;
  }

  function positionTourStep(index) {
    const { highlight, tooltip } = buildTourEls();
    const step = TOUR_STEPS[index];
    const el = $(step.target);
    if (!el) return;
    el.scrollIntoView({ block: "center", behavior: "smooth" });

    requestAnimationFrame(() => {
      const r = el.getBoundingClientRect();
      const pad = 10;
      highlight.style.top = `${r.top - pad}px`;
      highlight.style.left = `${r.left - pad}px`;
      highlight.style.width = `${r.width + pad * 2}px`;
      highlight.style.height = `${r.height + pad * 2}px`;

      const ttWidth = 280;
      let top = r.bottom + 16;
      let left = Math.min(Math.max(r.left, 12), window.innerWidth - ttWidth - 12);
      if (top + 160 > window.innerHeight) top = Math.max(r.top - 176, 12);
      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;

      tooltip.querySelector(".tour-eyebrow").textContent = step.eyebrow;
      tooltip.querySelector("h4").textContent = step.title;
      tooltip.querySelector(".tour-desc").textContent = step.text;
      tooltip.querySelector(".tour-stepcount").textContent = `${index + 1} of ${TOUR_STEPS.length}`;
      tooltip.querySelector(".tour-progress").innerHTML = TOUR_STEPS.map((_, i) => {
        const cls = i < index ? "done" : i === index ? "active" : "";
        return `<i class="${cls}" style="--step-ms:${TOUR_STEP_MS}ms"><b></b></i>`;
      }).join("");
    });
  }

  function startCreateTour() {
    const { scrim, highlight, tooltip } = buildTourEls();
    scrim.classList.add("show");
    highlight.classList.add("show");
    tooltip.classList.add("show");

    let i = 0;
    positionTourStep(i);
    tourTimer = setInterval(() => {
      i++;
      if (i >= TOUR_STEPS.length) { endCreateTour(); return; }
      positionTourStep(i);
    }, TOUR_STEP_MS);
  }

  function endCreateTour() {
    clearInterval(tourTimer);
    if (tourEls) {
      tourEls.scrim.classList.remove("show");
      tourEls.highlight.classList.remove("show");
      tourEls.tooltip.classList.remove("show");
    }
    try { localStorage.setItem(TOUR_SEEN_KEY, "1"); } catch (e) { /* private mode — ignore */ }
  }

  function maybeStartCreateTour() {
    let seen = false;
    try { seen = localStorage.getItem(TOUR_SEEN_KEY) === "1"; } catch (e) { /* ignore */ }
    if (seen) return;
    setTimeout(startCreateTour, 350); // let the view transition settle first
  }

  function openEditForm(evt) {
    editingEventId = evt.id;
    currentTicketDraft = structuredClone(evt.tickets);
    goTo("create");
    $("#eventFormTitle").textContent = `Edit "${evt.name}"`;
    $("#publishBtn").textContent = "Save Changes";

    $("#f_name").value = evt.name;
    $("#f_category").value = evt.category;
    $("#f_description").value = evt.description || "";
    $("#f_venue").value = evt.venue;
    $("#f_address").value = evt.address || "";
    $("#f_city").value = evt.city;
    $("#f_country").value = evt.country;
    $("#f_startDateTime").value = evt.startDateTime;
    $("#f_endDateTime").value = evt.endDateTime;
    $("#f_capacity").value = evt.capacity;
    $("#f_dresscode").value = evt.dresscode || "";
    $("#f_age").value = evt.age || "";
    $("#f_parking").checked = !!evt.parking;
    $("#f_food").checked = !!evt.food;
    $("#f_refund").value = evt.refund || "";
    $("#f_terms").checked = true;
    setBannerPreview(evt.banner || null);

    renderTicketDraft();
  }

  function readEventForm() {
    return {
      name: $("#f_name").value.trim(),
      category: $("#f_category").value,
      description: $("#f_description").value.trim(),
      venue: $("#f_venue").value.trim(),
      address: $("#f_address").value.trim(),
      city: $("#f_city").value.trim(),
      country: $("#f_country").value.trim(),
      startDateTime: $("#f_startDateTime").value,
      endDateTime: $("#f_endDateTime").value,
      capacity: Number($("#f_capacity").value) || 0,
      dresscode: $("#f_dresscode").value.trim(),
      age: $("#f_age").value.trim(),
      parking: $("#f_parking").checked,
      food: $("#f_food").checked,
      refund: $("#f_refund").value.trim(),
      tickets: currentTicketDraft
    };
  }

  function validateEventForm(data) {
    if (!data.name || !data.category || !data.venue || !data.city || !data.country) {
      toast("Please fill in all required fields marked with *", "danger");
      return false;
    }
    if (!data.startDateTime || !data.endDateTime) {
      toast("Please set the event date and time", "danger");
      return false;
    }
    if (new Date(data.endDateTime) < new Date(data.startDateTime)) {
      toast("Event end must be after the start", "danger");
      return false;
    }
    if (!$("#f_terms").checked) {
      toast("You must agree to the organizer Terms & Conditions", "danger");
      return false;
    }
    const used = data.tickets.reduce((s, t) => s + (Number(t.totalSeats) || 0), 0);
    if (data.capacity > 0 && used > data.capacity) {
      toast(`Ticket seats (${used}) exceed maximum capacity (${data.capacity})`, "danger");
      return false;
    }
    return true;
  }

  async function handleEventSubmit(e, status) {
    e.preventDefault();
    const data = readEventForm();
    data.status = status;
    if (status === "published" && !validateEventForm(data)) return;

    try {
      let savedEvent;
      if (editingEventId) {
        savedEvent = await api.events.update(editingEventId, data);
        toast("Event updated successfully", "success");
      } else {
        savedEvent = await api.events.create(data);
        toast(status === "draft" ? "Event saved as draft" : "Event published successfully", "success");
      }

      // Event Image Upload feature — only re-upload if the organizer picked a
      // NEW file in this session; leave an existing banner untouched otherwise.
      if (currentBannerFile && savedEvent?.id) {
        try {
          await api.events.uploadBanner(savedEvent.id, currentBannerFile);
        } catch (bannerErr) {
          console.error("Banner upload failed:", bannerErr);
          toast("Event saved, but the banner image failed to upload — you can try re-uploading it from Edit.", "danger");
        }
      }

      events = await api.events.list();
      refreshAllEventViews();
      resetEventForm();
      goTo("events");
    } catch (err) {
      console.error(err);
      toast("Couldn't save this event — please check your connection and try again.", "danger");
    }
  }

  function openPreview() {
    const data = readEventForm();
    const used = data.tickets.reduce((s, t) => s + (Number(t.totalSeats) || 0), 0);
    $("#previewBody").innerHTML = `
      <h3 style="margin:0 0 6px;">${data.name || "Untitled Event"}</h3>
      <p style="color:var(--muted);font-size:13.5px;margin:0 0 16px;">${data.description || "No description yet."}</p>
      <div class="detail-row"><span class="k">Category</span><span class="v">${data.category || "—"}</span></div>
      <div class="detail-row"><span class="k">Venue</span><span class="v">${data.venue || "—"}, ${data.city || "—"}</span></div>
      <div class="detail-row"><span class="k">Starts</span><span class="v">${data.startDateTime ? formatDateTime(data.startDateTime) : "—"}</span></div>
      <div class="detail-row"><span class="k">Ends</span><span class="v">${data.endDateTime ? formatDateTime(data.endDateTime) : "—"}</span></div>
      <div class="detail-row"><span class="k">Capacity</span><span class="v">${used} / ${data.capacity || 0} seats planned</span></div>
      <h4 style="margin:18px 0 10px;font-size:14px;">Ticket Categories</h4>
      <div class="ticket-categories">
        ${data.tickets.length ? data.tickets.map(t => `
          <div class="ticket-card">
            <div class="ticket-card-top">
              <span class="ticket-card-title"><span class="ticket-color-badge" style="background:${t.color}"></span>${t.name || "Untitled"}</span>
              <strong>${currency(t.price)}</strong>
            </div>
            <p style="font-size:12.5px;color:var(--muted);margin:0;">${t.benefits || "—"} · ${t.totalSeats || 0} seats</p>
          </div>`).join("") : `<div class="no-tickets-msg">No ticket categories added yet.</div>`}
      </div>`;
    openModal("previewModal");
  }

  /* ------------------------------------------------------------------ */
  /* Charts (pure vanilla — bar + donut)                                  */
  /* ------------------------------------------------------------------ */
  function renderBarChart(container, labels, values, valueFormatter = (v) => v) {
    const max = Math.max(...values, 1);
    container.innerHTML = `<div class="bar-chart">
      ${values.map((v, i) => `
        <div class="bar-col">
          <div class="bar-fill" style="height:0%" data-h="${Math.round((v / max) * 100)}" title="${valueFormatter(v)}"></div>
          <span class="bar-label">${labels[i]}</span>
        </div>`).join("")}
    </div>`;
    requestAnimationFrame(() => {
      $$(".bar-fill", container).forEach(el => { el.style.height = `${el.dataset.h}%`; });
    });
  }

  function buildSmoothPath(points) {
    if (points.length < 2) return `M ${points[0][0]} ${points[0][1]}`;
    let d = `M ${points[0][0]} ${points[0][1]}`;
    for (let i = 0; i < points.length - 1; i++) {
      const [x0, y0] = points[i];
      const [x1, y1] = points[i + 1];
      const mx = (x0 + x1) / 2;
      d += ` C ${mx} ${y0}, ${mx} ${y1}, ${x1} ${y1}`;
    }
    return d;
  }

  function renderLineChart(container, labels, values, valueFormatter = (v) => v) {
    const W = 600, H = 220, padX = 12, padY = 18;
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const range = (max - min) || 1;
    const stepX = (W - padX * 2) / Math.max(values.length - 1, 1);
    const points = values.map((v, i) => {
      const x = padX + i * stepX;
      const y = padY + (H - padY * 2) * (1 - (v - min) / range);
      return [x, y];
    });
    const linePath = buildSmoothPath(points);
    const areaPath = `${linePath} L ${points[points.length - 1][0]} ${H - padY} L ${points[0][0]} ${H - padY} Z`;
    const gid = uid("lg");

    container.innerHTML = `
      <div class="line-chart-wrap">
        <svg class="line-chart-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
          <defs>
            <linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--secondary)" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="var(--secondary)" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <path class="line-chart-area" d="${areaPath}" fill="url(#${gid})"></path>
          <path class="line-chart-path" d="${linePath}"></path>
          ${points.map(([x, y], i) => `<circle class="line-chart-dot" cx="${x}" cy="${y}" r="4.5" style="animation-delay:${1.05 + i * 0.05}s" data-value="${valueFormatter(values[i])}" data-x="${x}" data-y="${y}"></circle>`).join("")}
        </svg>
        <div class="line-chart-labels">${labels.map(l => `<span>${l}</span>`).join("")}</div>
        <div class="line-chart-tooltip"></div>
      </div>`;

    const wrap = $(".line-chart-wrap", container);
    const svg = $(".line-chart-svg", container);
    const path = $(".line-chart-path", container);
    const tooltip = $(".line-chart-tooltip", container);

    requestAnimationFrame(() => {
      const len = path.getTotalLength();
      path.style.setProperty("--len", len);
    });

    $$(".line-chart-dot", container).forEach(dot => {
      dot.addEventListener("mouseenter", () => {
        const rect = svg.getBoundingClientRect();
        const wrapRect = wrap.getBoundingClientRect();
        const scaleX = rect.width / W, scaleY = rect.height / H;
        const x = (rect.left - wrapRect.left) + parseFloat(dot.dataset.x) * scaleX;
        const y = (rect.top - wrapRect.top) + parseFloat(dot.dataset.y) * scaleY;
        tooltip.textContent = dot.dataset.value;
        tooltip.style.left = `${x}px`;
        tooltip.style.top = `${y}px`;
        tooltip.style.opacity = "1";
      });
      dot.addEventListener("mouseleave", () => { tooltip.style.opacity = "0"; });
    });
  }

  function renderDonutChart(container, segments) {
    const rawTotal = segments.reduce((s, x) => s + x.value, 0);
    if (rawTotal === 0) {
      container.innerHTML = `
        <div class="donut-wrap">
          <div class="donut-empty-ring">No sales yet</div>
          <div class="donut-legend">
            <div class="legend-row muted">Ticket sales will show up here once bookings start coming in.</div>
          </div>
        </div>`;
      return;
    }
    const total = rawTotal;
    let acc = 0;
    const stops = segments.map(seg => {
      const start = (acc / total) * 360;
      acc += seg.value;
      const end = (acc / total) * 360;
      return `${seg.color} ${start}deg ${end}deg`;
    }).join(", ");
    container.innerHTML = `
      <div class="donut-wrap">
        <div style="width:150px;height:150px;border-radius:50%;background:conic-gradient(${stops});flex-shrink:0;display:flex;align-items:center;justify-content:center;">
          <div style="width:88px;height:88px;border-radius:50%;background:var(--card);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;text-align:center;">${total}<br/><span style="font-weight:500;color:var(--muted);font-size:10px;">tickets</span></div>
        </div>
        <div class="donut-legend">
          ${segments.map(seg => `<div class="legend-row"><span class="legend-dot" style="background:${seg.color}"></span>${seg.label} · ${seg.value}</div>`).join("")}
        </div>
      </div>`;
  }

  function categorySalesBreakdown() {
    const map = {};
    events.forEach(e => e.tickets.forEach(t => { map[t.name] = (map[t.name] || 0) + (t.sold || 0); }));
    return Object.entries(map)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([label, value], i) => ({ label, value, color: TICKET_COLORS[i % TICKET_COLORS.length] }));
  }

  function renderDashboardCharts() {
    // mock 7-day revenue trend derived from current total revenue (a quick
    // illustrative glance — the Analytics/Revenue tabs pull the real
    // backend-computed trends instead)
    const total = computeStats().revenue || 50000;
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const weights = [0.08, 0.1, 0.12, 0.14, 0.18, 0.22, 0.16];
    const values = weights.map(w => Math.round(total * w));
    renderLineChart($("#revenueChart"), days, values, (v) => currency(v));
    renderDonutChart($("#categoryChart"), categorySalesBreakdown());
  }

  async function renderAnalyticsView() {
    try {
      const summary = await api.analytics.summary();
      $("#analyticsStats").innerHTML = [
        statCardHTML({ key: "tickets", label: "Tickets Sold", value: summary.tickets_sold, trend: 12, tint: "var(--accent-tint)", color: "#0891B2" }),
        statCardHTML({ key: "events", label: "Total Events", value: summary.total_events, trend: 8, tint: "var(--primary-tint)", color: "var(--primary)" }),
        statCardHTML({ key: "upcoming", label: "Upcoming Events", value: summary.upcoming_events, trend: 4, tint: "var(--secondary-tint)", color: "var(--secondary)" }),
        statCardHTML({ key: "revenue", label: "Total Revenue", value: summary.total_revenue, isCurrency: true, trend: 16, tint: "var(--success-tint)", color: "var(--success)" })
      ].join("");
      $$("[data-count]", $("#analyticsStats")).forEach(el => animateCounter(el, Number(el.dataset.target), el.dataset.currency === "true"));

      const salesData = await api.analytics.ticketSales(); // {"Mon": 5, "Tue": 12, ...}
      const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
      renderLineChart($("#ticketSalesChart"), days, days.map(d => salesData[d] || 0), (v) => `${v} tickets`);

      const categories = await api.analytics.popularCategories(); // {"VIP": 45, "General": 120}
      const colorEntries = Object.entries(categories).map(([label, value], i) => ({ label, value, color: TICKET_COLORS[i % TICKET_COLORS.length] }));
      renderDonutChart($("#categoryChart2"), colorEntries);
    } catch (err) {
      console.error(err);
      toast("Couldn't load analytics right now.", "danger");
    }
  }

  async function renderRevenueView() {
    try {
      const overview = await api.revenue.overview();
      $("#revenueStats").innerHTML = [
        statCardHTML({ key: "revenue", label: "Total Revenue", value: overview.total_revenue, isCurrency: true, trend: 16, tint: "var(--success-tint)", color: "var(--success)" }),
        statCardHTML({ key: "tickets", label: "Avg. Order Value", value: overview.avg_order_value, isCurrency: true, trend: 6, tint: "var(--accent-tint)", color: "#0891B2" }),
        statCardHTML({ key: "events", label: "Refunded", value: overview.refunded, isCurrency: true, trend: -3, tint: "var(--danger-tint)", color: "var(--danger)" }),
        statCardHTML({ key: "upcoming", label: "Net Revenue", value: overview.net_revenue, isCurrency: true, trend: 14, tint: "var(--secondary-tint)", color: "var(--secondary)" })
      ].join("");
      $$("[data-count]", $("#revenueStats")).forEach(el => animateCounter(el, Number(el.dataset.target), el.dataset.currency === "true"));

      const trend = await api.revenue.trend(); // {"Feb": 1000, "Mar": 1500, ...}
      const months = Object.keys(trend);
      renderLineChart($("#revenueTrendChart"), months, Object.values(trend), (v) => currency(v));
    } catch (err) {
      console.error(err);
      toast("Couldn't load revenue data right now.", "danger");
    }
  }

  /* ------------------------------------------------------------------ */
  /* Bookings table                                                       */
  /* ------------------------------------------------------------------ */
  function bookingRowHTML(b) {
    return `
    <tr>
      <td>${b.customer}</td>
      <td>${b.email}</td>
      <td>${b.category}${b.eventName ? ` · <span style="color:var(--muted)">${b.eventName}</span>` : ""}</td>
      <td>${b.qty}</td>
      <td>${currency(b.amount)}</td>
      <td>${formatDate(b.date)}</td>
      <td><span class="pay-${b.status}">${b.status[0].toUpperCase() + b.status.slice(1)}</span></td>
      <td class="${b.qr ? "qr-yes" : "qr-no"}">${b.qr ? "✔ Generated" : "—"}</td>
    </tr>`;
  }

  function renderBookingsTable(tbody, list) {
    tbody.innerHTML = list.map(bookingRowHTML).join("") || `<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px;">No bookings found.</td></tr>`;
  }

  function renderRecentBookings() {
    const tbody = $("#recentBookingsTable tbody");
    renderBookingsTable(tbody, bookings.slice(-5).reverse());
  }

  /* ------------------------------------------------------------------ */
  /* Fraud Detection (UI-only, no backend logic)                          */
  /* ------------------------------------------------------------------ */
  const FRAUD_STATUS_LABELS = { flagged: "Flagged", reviewing: "Under Review", confirmed: "Confirmed Fraud", dismissed: "Dismissed" };

  function riskLevel(score) {
    if (score >= 75) return "high";
    if (score >= 45) return "medium";
    return "low";
  }

  function riskBadgeHTML(score) {
    const level = riskLevel(score);
    const color = level === "high" ? "var(--danger)" : level === "medium" ? "var(--warning)" : "var(--success)";
    return `
      <div>
        <span class="risk-badge risk-${level}">${score}/100 · ${level[0].toUpperCase() + level.slice(1)}</span>
        <div class="risk-track"><div class="risk-track-fill" style="width:${score}%;background:${color}"></div></div>
      </div>`;
  }

  function fraudRowHTML(r) {
    return `
    <tr data-id="${r.id}">
      <td>${r.userName}</td>
      <td>${r.email}</td>
      <td>${r.eventName}</td>
      <td>${formatDate(r.bookingDate)}</td>
      <td style="max-width:240px;">${r.reason}</td>
      <td>${riskBadgeHTML(r.riskScore)}</td>
      <td><span class="fraud-status ${r.status}">${FRAUD_STATUS_LABELS[r.status] || r.status}</span></td>
      <td>
        <div class="fraud-actions">
          <button type="button" data-fraud-action="review" ${r.status === "reviewing" ? "disabled" : ""}>Mark Reviewing</button>
          <button type="button" class="confirm" data-fraud-action="confirm">Confirm Fraud</button>
          <button type="button" data-fraud-action="dismiss">Dismiss</button>
        </div>
      </td>
    </tr>`;
  }

  function renderFraudTable(list) {
    const wrap = $("#fraudTableWrap");
    const empty = $("#emptyStateFraud");
    if (!list.length) {
      wrap.hidden = true;
      empty.hidden = false;
      return;
    }
    wrap.hidden = false;
    empty.hidden = true;
    $("#fraudTable tbody").innerHTML = list.map(fraudRowHTML).join("");
  }

  function applyFraudFilters() {
    const q = ($("#fraudSearch")?.value || "").toLowerCase().trim();
    const risk = $("#fraudRiskFilter")?.value || "all";
    const status = $("#fraudStatusFilter")?.value || "all";
    const filtered = fraudRecords.filter(r => {
      const matchQ = !q || r.userName.toLowerCase().includes(q) || r.email.toLowerCase().includes(q) || r.eventName.toLowerCase().includes(q);
      const matchRisk = risk === "all" || riskLevel(r.riskScore) === risk;
      const matchStatus = status === "all" || r.status === status;
      return matchQ && matchRisk && matchStatus;
    });
    renderFraudTable(filtered);
  }

  function bindFraudTableActions() {
    $("#fraudTable tbody").addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-fraud-action]");
      if (!btn) return;
      const row = e.target.closest("tr[data-id]");
      const record = fraudRecords.find(r => r.id === row.dataset.id);
      if (!record) return;
      const action = btn.dataset.fraudAction;
      if (action === "review") record.status = "reviewing";
      if (action === "confirm") record.status = "confirmed";
      if (action === "dismiss") record.status = "dismissed";
      applyFraudFilters();
      toast(`Marked as ${FRAUD_STATUS_LABELS[record.status]}`, action === "confirm" ? "danger" : "success");
    });
  }

  /* ------------------------------------------------------------------ */
  /* Ticket management view (per-event picker)                            */
  /* ------------------------------------------------------------------ */
  function renderTicketEventPicker() {
    const wrap = $("#ticketEventPicker");
    wrap.innerHTML = events.map(e => {
      const sold = e.tickets.reduce((s, t) => s + (t.sold || 0), 0);
      return `<div class="ticket-picker-card" data-id="${e.id}">
        <h4>${e.name}</h4>
        <p>${e.tickets.length} categories · ${sold} tickets sold</p>
      </div>`;
    }).join("") || `<p style="color:var(--muted);">Create an event first to manage its ticket categories.</p>`;

    $$(".ticket-picker-card", wrap).forEach(card => {
      card.addEventListener("click", () => {
        const evt = events.find(e => e.id === card.dataset.id);
        openEditForm(evt);
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Notifications                                                        */
  /* ------------------------------------------------------------------ */
  const NOTIF_ICONS = {
    sold: { icon: `<svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/></svg>`, tint: "var(--secondary-tint)", color: "var(--secondary)" },
    published: { icon: `<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>`, tint: "var(--success-tint)", color: "var(--success)" },
    low: { icon: `<svg viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01"/></svg>`, tint: "var(--warning-tint)", color: "var(--warning)" },
    payment: { icon: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v10"/></svg>`, tint: "var(--success-tint)", color: "var(--success)" },
    refund: { icon: `<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>`, tint: "var(--danger-tint)", color: "var(--danger)" }
  };

  function renderNotifications(container, list, full = false) {
    container.innerHTML = list.map(n => {
      const meta = NOTIF_ICONS[n.type] || NOTIF_ICONS.sold;
      return `<div class="notif-item">
        <div class="notif-icon" style="background:${meta.tint};color:${meta.color}">${meta.icon}</div>
        <div class="notif-text"><p>${n.title}</p><small>${n.body} · ${n.time}</small></div>
      </div>`;
    }).join("") || `<p style="padding:20px;color:var(--muted);">You're all caught up.</p>`;
  }

  /* ------------------------------------------------------------------ */
  /* Refresh helpers                                                      */
  /* ------------------------------------------------------------------ */
  function refreshAllEventViews() {
    renderStats($("#statsGrid"));
    renderEventsGrid();
    renderDashboardCharts();
    renderRecentBookings();
  }

  /* ------------------------------------------------------------------ */
  /* Global UI bindings                                                   */
  /* ------------------------------------------------------------------ */
  function bindGlobalUI() {
    // Sidebar nav
    $$(".nav-item[data-view]").forEach(item => {
      item.addEventListener("click", (e) => {
        e.preventDefault();
        goTo(item.dataset.view);
      });
    });
    $$("[data-view-link]").forEach(el => {
      el.addEventListener("click", (e) => { e.preventDefault(); goTo(el.dataset.viewLink); });
    });

    // Mobile sidebar
    $("#menuToggle").addEventListener("click", () => {
      $("#sidebar").classList.add("open");
      $("#sidebarOverlay").classList.add("open");
    });
    $("#sidebarClose").addEventListener("click", closeSidebarMobile);
    $("#sidebarOverlay").addEventListener("click", closeSidebarMobile);

    // Dropdowns
    function toggleDropdown(btnId, wrapSelector) {
      const btn = $(`#${btnId}`);
      const wrap = btn.closest(".dropdown-wrap") || $(wrapSelector);
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = wrap.classList.contains("open");
        $$(".dropdown-wrap.open").forEach(w => w.classList.remove("open"));
        if (!isOpen) wrap.classList.add("open");
      });
    }
    toggleDropdown("notifBtn");
    toggleDropdown("profileBtn");
    document.addEventListener("click", () => $$(".dropdown-wrap.open").forEach(w => w.classList.remove("open")));

    // Logout
    [$("#logoutBtn"), $("#logoutBtn2")].forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        toast("Logging out…");
        localStorage.removeItem("access_token");
        setTimeout(() => { window.location.href = "../login_sign_in/login.html"; }, 700);
      });
    });

    // New event buttons
    [$("#newEventBtn"), $("#newEventBtn2"), $("#emptyCreateBtn"), $("#emptyCreateBtn2")].forEach(btn => {
      btn.addEventListener("click", () => { resetEventForm(); goTo("create"); });
    });

    // Event grid actions (both grids share the same handler)
    bindEventCardActions($("#eventsGrid"));
    bindEventCardActions($("#eventsGridFull"));

    // Modal closers
    $$("[data-close-modal]").forEach(btn => {
      btn.addEventListener("click", () => closeModal(btn.dataset.closeModal));
    });
    $$(".modal-overlay").forEach(overlay => {
      overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("open"); });
    });

    $("#confirmDeleteBtn").addEventListener("click", async () => {
      if (!pendingDeleteId) return;
      try {
        await api.events.remove(pendingDeleteId);
        events = await api.events.list();
        refreshAllEventViews();
        closeModal("deleteModal");
        toast("Event deleted", "danger");
      } catch (err) {
        console.error(err);
        toast("Couldn't delete this event — please try again.", "danger");
      } finally {
        pendingDeleteId = null;
      }
    });

    // Clear all notifications
    $("#clearNotifsBtn").addEventListener("click", () => {
      if (!notifications.length) {
        toast("No notifications to clear.");
        return;
      }
      openModal("clearNotifsModal");
    });

    $("#confirmClearNotifsBtn").addEventListener("click", async () => {
      try {
        await api.notifications.clearAll();
        notifications = [];
        renderNotifications($("#notifList"), notifications.slice(0, 4));
        renderNotifications($("#notifListFull"), notifications, true);
        closeModal("clearNotifsModal");
        toast("All notifications cleared", "danger");
      } catch (err) {
        console.error(err);
        toast("Couldn't clear notifications — please try again.", "danger");
      }
    });

    // Filters / search / sort
    ["eventSearch", "filterStatus", "filterCategory", "sortBy"].forEach(id => {
      const el = $(`#${id}`);
      if (el) el.addEventListener("input", renderEventsGrid);
    });
    const search2 = $("#eventSearch2");
    if (search2) search2.addEventListener("input", () => {
      $("#eventSearch").value = search2.value;
      renderEventsGrid();
    });
    const status2 = $("#filterStatus2");
    if (status2) status2.addEventListener("change", () => {
      $("#filterStatus").value = status2.value;
      renderEventsGrid();
    });

    // Global search -> jump to events view and filter
    $("#globalSearch").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        $("#eventSearch").value = e.target.value;
        goTo("events");
        renderEventsGrid();
      }
    });

    // Bookings search/filter
    const bookingSearch = $("#bookingSearch");
    const bookingStatusFilter = $("#bookingStatusFilter");
    function applyBookingFilters() {
      const q = bookingSearch.value.toLowerCase().trim();
      const status = bookingStatusFilter.value;
      const filtered = bookings.filter(b => {
        const matchQ = !q || b.customer.toLowerCase().includes(q) || b.email.toLowerCase().includes(q);
        const matchStatus = status === "all" || b.status === status;
        return matchQ && matchStatus;
      });
      renderBookingsTable($("#bookingsTable tbody"), filtered);
    }
    bookingSearch.addEventListener("input", applyBookingFilters);
    bookingStatusFilter.addEventListener("change", applyBookingFilters);

    // Fraud detection filters
    ["fraudSearch", "fraudRiskFilter", "fraudStatusFilter"].forEach(id => {
      const el = $(`#${id}`);
      el.addEventListener("input", applyFraudFilters);
      el.addEventListener("change", applyFraudFilters);
    });
    bindFraudTableActions();

    // Ticket categories in form
    $("#addTicketCategoryBtn").addEventListener("click", () => {
      currentTicketDraft.push(newTicketCategory());
      renderTicketDraft();
    });
    bindTicketDraftEvents();
    bindBannerUpload();

    // Form submit / draft / preview
    $("#eventForm").addEventListener("submit", (e) => handleEventSubmit(e, "published"));
    $("#saveDraftBtn").addEventListener("click", (e) => handleEventSubmit(e, "draft"));
    $("#previewBtn").addEventListener("click", openPreview);
  }

  /* ------------------------------------------------------------------ */
  /* Logged-in organizer identity                                         */
  /* ------------------------------------------------------------------ */
  function applyOrganizerIdentity(user) {
    const name = (user && user.full_name) || "Organizer";
    const firstName = name.split(" ")[0];
    const initials = getInitials(name);

    $("#welcomeName").textContent = `${firstName} 👋`;
    $("#topbarAvatar").textContent = initials;
    $("#topbarUserName").textContent = name;
    $("#profileAvatarLarge").textContent = initials;
    $("#profileNameInput").value = name;
    $("#profileEmailInput").value = (user && user.email) || "";
    $("#profilePhoneInput").value = (user && user.phone) || "";
    $("#profileCompanyInput").value = (user && user.company) || "";
  }

  /* ------------------------------------------------------------------ */
  /* Welcome section                                                      */
  /* ------------------------------------------------------------------ */
  function renderWelcome() {
    const hour = new Date().getHours();
    const greeting = hour < 12 ? "Good Morning," : hour < 18 ? "Good Afternoon," : "Good Evening,";
    $("#greetingLine").textContent = greeting;
    $("#todayDate").textContent = new Date().toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  }

  /* ------------------------------------------------------------------ */
  /* Init                                                                 */
  /* ------------------------------------------------------------------ */
  async function init() {
    if (!localStorage.getItem("access_token")) {
      window.location.href = "../login_sign_in/login.html";
      return;
    }


    // Back button = force logout (Shahryar's requirement)
    history.pushState(null, '', location.href);
    window.addEventListener('popstate', () => {
      localStorage.removeItem('access_token');
      window.location.replace('../login_sign_in/login.html');
    });

    renderWelcome();
    bindGlobalUI();

    try {
      currentUser = await api.auth.me();
      if (!currentUser.role_selected) {
        window.location.href = "../role/index.html";
        return;
      }
      if (currentUser.role !== "organizer") {
        window.location.href = "../customer-window/index.html";
        return;
      }
    } catch (err) {
      console.error(err);
      toast("Couldn't verify your account — please log in again.", "danger");
      localStorage.removeItem("access_token");
      window.location.href = "../login_sign_in/login.html";
      return;
    }
    applyOrganizerIdentity(currentUser);

    try {
      events = await api.events.list();
      bookings = await api.bookings.list();
      notifications = await api.notifications.list();
      fraudRecords = await api.fraud.list();
    } catch (err) {
      console.error(err);
      toast("Couldn't reach the server — some data may be missing.", "danger");
      events = events.length ? events : [];
      bookings = bookings.length ? bookings : [];
      notifications = notifications.length ? notifications : [];
      fraudRecords = fraudRecords.length ? fraudRecords : [];
    }

    refreshAllEventViews();
    renderNotifications($("#notifList"), notifications.slice(0, 4));
    renderTicketEventPicker();

    const initialView = (location.hash || "#dashboard").replace("#", "");
    goTo(VIEW_META[initialView] ? initialView : "dashboard");
  }

  document.addEventListener("DOMContentLoaded", init);
})();