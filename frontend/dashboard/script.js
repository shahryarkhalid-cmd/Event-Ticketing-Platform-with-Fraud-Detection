/* ==========================================================================
   Tixora Organizer Dashboard — Application Logic
   Architecture note:
   All data operations go through the `api` object below. Right now `api`
   resolves against an in-memory store so the dashboard works standalone.
   Every method already mirrors a REST call (method + endpoint shown in
   comments), so swapping the internals for real `fetch()` calls to your
   Node/Express + PostgreSQL backend will not require touching any of the
   rendering or event-handling code elsewhere in this file.
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
  const delay = (ms = 250) => new Promise((res) => setTimeout(res, ms));

  function formatDate(d) {
    const date = new Date(d);
    if (isNaN(date)) return d;
    return date.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
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

  /* ------------------------------------------------------------------ */
  /* Seed / mock data (stand-in for real database rows)                   */
  /* ------------------------------------------------------------------ */
  const store = {
    events: [
      {
        id: uid("evt"), name: "Lahore Music Fest", category: "Concert", status: "live",
        description: "An open-air night of live music across three stages.",
        venue: "Fortress Stadium", city: "Lahore", country: "Pakistan", address: "Fortress Stadium, Lahore Cantt",
        startDate: "2026-08-14", endDate: "2026-08-14", startTime: "17:00", endTime: "23:30",
        capacity: 5000, dresscode: "Casual", age: "13+", parking: true, food: true,
        refund: "Full refund up to 7 days before the event.", poster: "",
        tickets: [
          { id: uid("tkt"), name: "General", price: 1200, currency: "PKR", totalSeats: 3000, availableSeats: 900, sold: 2100, description: "Standard entry", benefits: "Standard Entry", color: TICKET_COLORS[0], salesStart: "2026-06-01", salesEnd: "2026-08-13", maxPerPerson: 6 },
          { id: uid("tkt"), name: "VIP", price: 5000, currency: "PKR", totalSeats: 1500, availableSeats: 300, sold: 1200, description: "Front row access", benefits: "Front Row, Free Drinks, VIP Lounge", color: TICKET_COLORS[1], salesStart: "2026-06-01", salesEnd: "2026-08-13", maxPerPerson: 4 },
          { id: uid("tkt"), name: "VVIP", price: 9000, currency: "PKR", totalSeats: 500, availableSeats: 40, sold: 460, description: "All-access backstage", benefits: "Backstage, Meet & Greet, Free Drinks", color: TICKET_COLORS[2], salesStart: "2026-06-01", salesEnd: "2026-08-13", maxPerPerson: 2 }
        ]
      },
      {
        id: uid("evt"), name: "Founders Summit 2026", category: "Conference", status: "upcoming",
        description: "A day of talks with operators and investors building in Pakistan.",
        venue: "Pearl Continental", city: "Karachi", country: "Pakistan", address: "Club Road, Karachi",
        startDate: "2026-09-02", endDate: "2026-09-02", startTime: "09:00", endTime: "18:00",
        capacity: 800, dresscode: "Smart Casual", age: "18+", parking: true, food: true,
        refund: "50% refund up to 14 days before the event.", poster: "",
        tickets: [
          { id: uid("tkt"), name: "General", price: 3500, currency: "PKR", totalSeats: 600, availableSeats: 380, sold: 220, description: "Full day access", benefits: "Full Access, Lunch", color: TICKET_COLORS[0], salesStart: "2026-06-15", salesEnd: "2026-09-01", maxPerPerson: 3 },
          { id: uid("tkt"), name: "Premium", price: 7500, currency: "PKR", totalSeats: 200, availableSeats: 120, sold: 80, description: "Front-row + networking dinner", benefits: "Front Row, Networking Dinner", color: TICKET_COLORS[3], salesStart: "2026-06-15", salesEnd: "2026-09-01", maxPerPerson: 2 }
        ]
      },
      {
        id: uid("evt"), name: "Comedy Night Vol. 3", category: "Comedy", status: "draft",
        description: "An evening of stand-up from the country's sharpest comics.",
        venue: "Alhamra Arts Council", city: "Lahore", country: "Pakistan", address: "The Mall, Lahore",
        startDate: "2026-10-05", endDate: "2026-10-05", startTime: "20:00", endTime: "22:30",
        capacity: 600, dresscode: "Casual", age: "16+", parking: false, food: false,
        refund: "No refunds within 48 hours of the event.", poster: "",
        tickets: [
          { id: uid("tkt"), name: "General", price: 1500, currency: "PKR", totalSeats: 600, availableSeats: 600, sold: 0, description: "Standard entry", benefits: "Standard Entry", color: TICKET_COLORS[0], salesStart: "2026-09-01", salesEnd: "2026-10-04", maxPerPerson: 5 }
        ]
      },
      {
        id: uid("evt"), name: "Karachi Marathon", category: "Sports", status: "finished",
        description: "A 10k community run along the seafront.",
        venue: "Sea View", city: "Karachi", country: "Pakistan", address: "Sea View Beach",
        startDate: "2026-05-10", endDate: "2026-05-10", startTime: "06:00", endTime: "10:00",
        capacity: 2000, dresscode: "Sportswear", age: "All ages", parking: true, food: true,
        refund: "Non-refundable.", poster: "",
        tickets: [
          { id: uid("tkt"), name: "Runner", price: 800, currency: "PKR", totalSeats: 2000, availableSeats: 0, sold: 2000, description: "Race pack included", benefits: "Race Pack, Medal", color: TICKET_COLORS[0], salesStart: "2026-03-01", salesEnd: "2026-05-09", maxPerPerson: 1 }
        ]
      }
    ],
    bookings: [
      { id: uid("bk"), customer: "Sara Khan", email: "sara.khan@example.com", eventName: "Lahore Music Fest", category: "VIP", qty: 2, amount: 10000, date: "2026-07-18", status: "paid", qr: true },
      { id: uid("bk"), customer: "Bilal Ahmed", email: "bilal.a@example.com", eventName: "Lahore Music Fest", category: "General", qty: 4, amount: 4800, date: "2026-07-19", status: "paid", qr: true },
      { id: uid("bk"), customer: "Ayesha Noor", email: "ayesha.noor@example.com", eventName: "Founders Summit 2026", category: "Premium", qty: 1, amount: 7500, date: "2026-07-19", status: "pending", qr: false },
      { id: uid("bk"), customer: "Hamza Tariq", email: "hamza.t@example.com", eventName: "Lahore Music Fest", category: "VVIP", qty: 1, amount: 9000, date: "2026-07-20", status: "refunded", qr: false },
      { id: uid("bk"), customer: "Mehak Ali", email: "mehak.ali@example.com", eventName: "Founders Summit 2026", category: "General", qty: 2, amount: 7000, date: "2026-07-20", status: "paid", qr: true },
      { id: uid("bk"), customer: "Usman Sheikh", email: "usman.sheikh@example.com", eventName: "Karachi Marathon", category: "Runner", qty: 1, amount: 800, date: "2026-07-21", status: "paid", qr: true }
    ],
    notifications: [
      { id: uid("nt"), type: "sold", title: "12 tickets sold", body: "Lahore Music Fest · VIP category", time: "5 min ago" },
      { id: uid("nt"), type: "published", title: "Event published", body: "Founders Summit 2026 is now live for booking", time: "2 hours ago" },
      { id: uid("nt"), type: "low", title: "Low ticket alert", body: "VVIP — only 40 seats left for Lahore Music Fest", time: "3 hours ago" },
      { id: uid("nt"), type: "payment", title: "Payment received", body: "PKR 7,500 from Ayesha Noor", time: "Yesterday" },
      { id: uid("nt"), type: "refund", title: "Refund requested", body: "Hamza Tariq requested a refund for VVIP", time: "Yesterday" }
    ]
  };

  /* ------------------------------------------------------------------ */
  /* API layer (swap-ready for a real backend)                           */
  /* ------------------------------------------------------------------ */
  const api = {
    events: {
      // GET /api/events
      async list() { await delay(); return structuredClone(store.events); },
      // GET /api/events/:id
      async get(id) { await delay(120); return structuredClone(store.events.find(e => e.id === id)); },
      // POST /api/events
      async create(payload) {
        await delay();
        const evt = { ...payload, id: uid("evt") };
        store.events.unshift(evt);
        return structuredClone(evt);
      },
      // PUT /api/events/:id
      async update(id, payload) {
        await delay();
        const idx = store.events.findIndex(e => e.id === id);
        if (idx > -1) store.events[idx] = { ...store.events[idx], ...payload, id };
        return structuredClone(store.events[idx]);
      },
      // DELETE /api/events/:id
      async remove(id) {
        await delay();
        store.events = store.events.filter(e => e.id !== id);
        return { success: true };
      }
    },
    bookings: {
      // GET /api/bookings
      async list() { await delay(); return structuredClone(store.bookings); }
    },
    notifications: {
      // GET /api/notifications
      async list() { await delay(120); return structuredClone(store.notifications); }
    }
  };

  /* ------------------------------------------------------------------ */
  /* App state                                                            */
  /* ------------------------------------------------------------------ */
  let events = [];
  let bookings = [];
  let notifications = [];
  let currentTicketDraft = []; // ticket categories being edited in the Create/Edit form
  let editingEventId = null;
  let pendingDeleteId = null;

  /* ------------------------------------------------------------------ */
  /* Navigation / routing                                                 */
  /* ------------------------------------------------------------------ */
  const VIEW_META = {
    dashboard: { title: "Dashboard", crumb: "Overview" },
    events: { title: "My Events", crumb: "All Events" },
    create: { title: "Create Event", crumb: "New Event" },
    tickets: { title: "Manage Tickets", crumb: "Ticket Categories" },
    bookings: { title: "Bookings", crumb: "All Bookings" },
    analytics: { title: "Analytics", crumb: "Performance" },
    revenue: { title: "Revenue", crumb: "Earnings" },
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

    if (view === "create" && editingEventId === null) resetEventForm();
    if (view === "tickets") renderTicketEventPicker();
    if (view === "bookings") renderBookingsTable($("#bookingsTable tbody"), bookings);
    if (view === "notifications") renderNotifications($("#notifListFull"), notifications, true);
    if (view === "analytics") renderAnalyticsView();
    if (view === "revenue") renderRevenueView();

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
    const totalEvents = events.length;
    const upcoming = events.filter(e => e.status === "upcoming" || e.status === "live").length;
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
      <div class="event-poster" role="img" aria-label="${evt.name} banner"></div>
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
          ${formatDate(evt.startDate)} · ${evt.startTime}
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

    const html = filtered.map(eventCardHTML).join("");
    if (grid) grid.innerHTML = html;
    if (gridFull) gridFull.innerHTML = html;

    if (empty) empty.hidden = events.length !== 0;
    if (grid) grid.hidden = events.length === 0;

    // populate category filter dynamically
    const catSelect = $("#filterCategory");
    if (catSelect && catSelect.children.length <= 1) {
      const cats = [...new Set(events.map(e => e.category))];
      cats.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c; opt.textContent = c;
        catSelect.appendChild(opt);
      });
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
    copy.status = "draft";
    copy.tickets = copy.tickets.map(t => ({ ...t, id: uid("tkt"), sold: 0, availableSeats: t.totalSeats }));
    const created = await api.events.create(copy);
    events = await api.events.list();
    refreshAllEventViews();
    toast(`Duplicated "${evt.name}"`, "success");
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
      <div class="detail-row"><span class="k">Date</span><span class="v">${formatDate(evt.startDate)} – ${formatDate(evt.endDate)}</span></div>
      <div class="detail-row"><span class="k">Time</span><span class="v">${evt.startTime} – ${evt.endTime}</span></div>
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
    $("#eventForm").reset();
    $("#eventFormTitle").textContent = "Create Event";
    $("#publishBtn").textContent = "Publish Event";
    renderTicketDraft();
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
    $("#f_startDate").value = evt.startDate;
    $("#f_endDate").value = evt.endDate;
    $("#f_startTime").value = evt.startTime;
    $("#f_endTime").value = evt.endTime;
    $("#f_capacity").value = evt.capacity;
    $("#f_dresscode").value = evt.dresscode || "";
    $("#f_age").value = evt.age || "";
    $("#f_parking").checked = !!evt.parking;
    $("#f_food").checked = !!evt.food;
    $("#f_refund").value = evt.refund || "";
    $("#f_terms").checked = true;

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
      startDate: $("#f_startDate").value,
      endDate: $("#f_endDate").value,
      startTime: $("#f_startTime").value,
      endTime: $("#f_endTime").value,
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
    if (!data.startDate || !data.endDate || !data.startTime || !data.endTime) {
      toast("Please set the event date and time", "danger");
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

    if (editingEventId) {
      await api.events.update(editingEventId, data);
      toast("Event updated successfully", "success");
    } else {
      await api.events.create(data);
      toast(status === "draft" ? "Event saved as draft" : "Event published successfully", "success");
    }
    events = await api.events.list();
    refreshAllEventViews();
    resetEventForm();
    goTo("events");
  }

  function openPreview() {
    const data = readEventForm();
    const used = data.tickets.reduce((s, t) => s + (Number(t.totalSeats) || 0), 0);
    $("#previewBody").innerHTML = `
      <h3 style="margin:0 0 6px;">${data.name || "Untitled Event"}</h3>
      <p style="color:var(--muted);font-size:13.5px;margin:0 0 16px;">${data.description || "No description yet."}</p>
      <div class="detail-row"><span class="k">Category</span><span class="v">${data.category || "—"}</span></div>
      <div class="detail-row"><span class="k">Venue</span><span class="v">${data.venue || "—"}, ${data.city || "—"}</span></div>
      <div class="detail-row"><span class="k">Date</span><span class="v">${data.startDate ? formatDate(data.startDate) : "—"} – ${data.endDate ? formatDate(data.endDate) : "—"}</span></div>
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

  function renderDonutChart(container, segments) {
    const total = segments.reduce((s, x) => s + x.value, 0) || 1;
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
    // mock 7-day revenue trend derived from current total revenue
    const total = computeStats().revenue || 50000;
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const weights = [0.08, 0.1, 0.12, 0.14, 0.18, 0.22, 0.16];
    const values = weights.map(w => Math.round(total * w));
    renderBarChart($("#revenueChart"), days, values, (v) => currency(v));
    renderDonutChart($("#categoryChart"), categorySalesBreakdown());
  }

  function renderAnalyticsView() {
    const s = computeStats();
    $("#analyticsStats").innerHTML = [
      statCardHTML({ key: "tickets", label: "Tickets Sold", value: s.ticketsSold, trend: 12, tint: "var(--accent-tint)", color: "#0891B2" }),
      statCardHTML({ key: "events", label: "Total Events", value: s.totalEvents, trend: 8, tint: "var(--primary-tint)", color: "var(--primary)" }),
      statCardHTML({ key: "upcoming", label: "Upcoming Events", value: s.upcoming, trend: 4, tint: "var(--secondary-tint)", color: "var(--secondary)" }),
      statCardHTML({ key: "revenue", label: "Total Revenue", value: s.revenue, isCurrency: true, trend: 16, tint: "var(--success-tint)", color: "var(--success)" })
    ].join("");
    $$("[data-count]", $("#analyticsStats")).forEach(el => animateCounter(el, Number(el.dataset.target), el.dataset.currency === "true"));

    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const ticketWeights = [8, 14, 10, 18, 22, 30, 20];
    renderBarChart($("#ticketSalesChart"), days, ticketWeights, (v) => `${v} tickets`);
    const visitorWeights = [120, 180, 150, 210, 260, 340, 280];
    renderBarChart($("#visitorsChart"), days, visitorWeights, (v) => `${v} visitors`);
    renderDonutChart($("#categoryChart2"), categorySalesBreakdown());
  }

  function renderRevenueView() {
    const s = computeStats();
    const avgOrder = bookings.length ? Math.round(bookings.reduce((sum, b) => sum + b.amount, 0) / bookings.length) : 0;
    const refunded = bookings.filter(b => b.status === "refunded").reduce((sum, b) => sum + b.amount, 0);
    $("#revenueStats").innerHTML = [
      statCardHTML({ key: "revenue", label: "Total Revenue", value: s.revenue, isCurrency: true, trend: 16, tint: "var(--success-tint)", color: "var(--success)" }),
      statCardHTML({ key: "tickets", label: "Avg. Order Value", value: avgOrder, isCurrency: true, trend: 6, tint: "var(--accent-tint)", color: "#0891B2" }),
      statCardHTML({ key: "events", label: "Refunded", value: refunded, isCurrency: true, trend: -3, tint: "var(--danger-tint)", color: "var(--danger)" }),
      statCardHTML({ key: "upcoming", label: "Net Revenue", value: s.revenue - refunded, isCurrency: true, trend: 14, tint: "var(--secondary-tint)", color: "var(--secondary)" })
    ].join("");
    $$("[data-count]", $("#revenueStats")).forEach(el => animateCounter(el, Number(el.dataset.target), el.dataset.currency === "true"));

    const months = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"];
    const total = s.revenue || 60000;
    const weights = [0.1, 0.12, 0.15, 0.18, 0.2, 0.25];
    renderBarChart($("#revenueTrendChart"), months, weights.map(w => Math.round(total * w)), (v) => currency(v));
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
        setTimeout(() => { window.location.href = "index.html"; }, 700);
      });
    });

    // New event buttons
    [$("#newEventBtn"), $("#newEventBtn2"), $("#emptyCreateBtn")].forEach(btn => {
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
      await api.events.remove(pendingDeleteId);
      events = await api.events.list();
      refreshAllEventViews();
      closeModal("deleteModal");
      toast("Event deleted", "danger");
      pendingDeleteId = null;
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

    // Ticket categories in form
    $("#addTicketCategoryBtn").addEventListener("click", () => {
      currentTicketDraft.push(newTicketCategory());
      renderTicketDraft();
    });
    bindTicketDraftEvents();

    // Form submit / draft / preview
    $("#eventForm").addEventListener("submit", (e) => handleEventSubmit(e, "published"));
    $("#saveDraftBtn").addEventListener("click", (e) => handleEventSubmit(e, "draft"));
    $("#previewBtn").addEventListener("click", openPreview);
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
    renderWelcome();
    bindGlobalUI();

    events = await api.events.list();
    bookings = await api.bookings.list();
    notifications = await api.notifications.list();

    refreshAllEventViews();
    renderNotifications($("#notifList"), notifications.slice(0, 4));
    renderTicketEventPicker();

    const initialView = (location.hash || "#dashboard").replace("#", "");
    goTo(VIEW_META[initialView] ? initialView : "dashboard");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
