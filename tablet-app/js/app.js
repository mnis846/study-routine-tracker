(function () {
  const { loadState, saveState, exportJson, importJson } = window.SRTDB;
  const L = window.SRTLogic;

  let state = null;
  let page = "today";
  let deferredInstall = null;

  const $ = (sel) => document.querySelector(sel);
  const pages = {
    today: $("#page-today"),
    hours: $("#page-hours"),
    notes: $("#page-notes"),
    garden: $("#page-garden"),
    more: $("#page-more"),
  };

  function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.remove("show"), 2200);
  }

  async function persist() {
    await saveState(state);
  }

  function setPage(name) {
    page = name;
    Object.entries(pages).forEach(([k, el]) => {
      el.classList.toggle("hidden", k !== name);
    });
    document.querySelectorAll(".nav button").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.page === name);
    });
    render();
    window.scrollTo(0, 0);
  }

  function openSheet(id) {
    $("#sheet-backdrop").classList.add("open");
    $(id).classList.add("open");
  }

  function closeSheets() {
    $("#sheet-backdrop").classList.remove("open");
    document.querySelectorAll(".sheet").forEach((s) => s.classList.remove("open"));
  }

  function planFor(date) {
    if (!state.plans[date]) state.plans[date] = { items: [] };
    return state.plans[date];
  }

  function renderHeader() {
    const today = L.todayISO();
    $("#greet-name").textContent = state.name || "Student";
    $("#greet-date").textContent = new Date().toLocaleDateString(undefined, {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
    const streak = L.studyStreak(state, today);
    const goalStreak = L.goalStreak(state, today);
    const todayH = L.hoursOn(state, today);
    const goal = Number(state.dailyGoal) || 6;
    const goalLabel = Number.isInteger(goal) ? String(goal) : String(goal);
    $("#stat-streak").textContent = String(streak);
    $("#stat-goal").textContent = `${goalLabel}h`;
    $("#stat-today").textContent = `${todayH}h`;
    $("#stat-xp").textContent = String(state.gardenXp || 0);
    const treesEl = $("#stat-trees");
    if (treesEl) treesEl.textContent = String(L.treeCount(goalStreak));
  }

  function renderWelcome() {
    const box = $("#welcome");
    if (state.welcomeSeen) {
      box.classList.add("hidden");
      return;
    }
    box.classList.remove("hidden");
  }

  function renderToday() {
    const today = L.todayISO();
    const plan = planFor(today);
    const list = $("#today-list");
    list.innerHTML = "";

    if (!plan.items.length) {
      list.innerHTML = `<p class="muted">No plan yet. Add 1–3 things to study today.</p>`;
    }

    plan.items.forEach((item) => {
      const div = document.createElement("div");
      div.className = `target ${item.status === "Done" ? "done" : ""} ${item.status === "Skipped" ? "skipped" : ""}`;
      div.innerHTML = `
        <input type="checkbox" ${item.status === "Done" ? "checked" : ""} ${item.status === "Skipped" ? "disabled" : ""} />
        <div class="body">
          <div class="text">${escapeHtml(item.text)}</div>
          <div class="btn-row" style="margin-top:8px;grid-template-columns:1fr">
            ${
              item.status === "Skipped"
                ? `<button class="ghost" data-act="unskip">Undo skip</button>`
                : item.status === "Done"
                  ? ""
                  : `<button class="ghost" data-act="skip">Skip</button>`
            }
          </div>
        </div>`;
      const cb = div.querySelector('input[type="checkbox"]');
      cb?.addEventListener("change", async () => {
        const wasDone = item.status === "Done";
        item.status = cb.checked ? "Done" : "Pending";
        if (cb.checked && !wasDone) {
          L.awardTargetDone(state);
          const allDone = plan.items.every((i) => i.status === "Done" || i.status === "Skipped");
          const anyDone = plan.items.some((i) => i.status === "Done");
          if (allDone && anyDone) L.awardAllTargets(state, today);
          toast("Nice — item done · garden grew");
        }
        await persist();
        render();
      });
      div.querySelector('[data-act="skip"]')?.addEventListener("click", async () => {
        item.status = "Skipped";
        await persist();
        render();
      });
      div.querySelector('[data-act="unskip"]')?.addEventListener("click", async () => {
        item.status = "Pending";
        await persist();
        render();
      });
      list.appendChild(div);
    });

    const done = plan.items.filter((i) => i.status === "Done").length;
    const total = plan.items.length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    $("#today-progress").style.width = `${pct}%`;
    $("#today-progress-label").textContent = total
      ? `${done} of ${total} done`
      : "Add items to start";
  }

  function renderHours() {
    const today = L.todayISO();
    const goal = Number(state.dailyGoal) || 6;
    const todayH = L.hoursOn(state, today);
    const pct = Math.min(100, Math.round((todayH / goal) * 100));
    $("#hours-today").textContent = `${todayH}h / ${goal}h`;
    $("#hours-progress").style.width = `${pct}%`;

    const week = L.weekHours(state, today);
    const maxH = Math.max(goal, ...week.map((w) => w.hours), 1);
    const bars = $("#week-bars");
    bars.innerHTML = "";
    week.forEach((w) => {
      const h = Math.max(4, Math.round((w.hours / maxH) * 100));
      const label = new Date(w.date + "T12:00:00").toLocaleDateString(undefined, { weekday: "short" });
      const wrap = document.createElement("div");
      wrap.className = "bar-wrap";
      wrap.innerHTML = `<div class="bar ${w.isToday ? "today" : ""}" style="height:${w.hours ? h : 4}%"></div><span class="dlabel">${label}</span>`;
      bars.appendChild(wrap);
    });

    // heatmap
    const cells = L.heatmapDays(state, 119, today);
    const heat = $("#heatmap");
    heat.innerHTML = "";
    cells.forEach((c) => {
      const i = document.createElement("i");
      i.className = `l${c.level}${c.isToday ? " today" : ""}`;
      i.title = `${c.date}: ${c.hours}h`;
      heat.appendChild(i);
    });
  }

  function renderNotes() {
    const list = $("#notes-list");
    list.innerHTML = "";
    const notes = (state.notes || []).slice(0, 40);
    if (!notes.length) {
      list.innerHTML = `<p class="muted">No notes yet. Write one short line after studying.</p>`;
      return;
    }
    notes.forEach((n) => {
      const div = document.createElement("div");
      div.className = "list-note";
      div.innerHTML = `
        <div class="meta">${escapeHtml(n.date)} · ${escapeHtml(n.subject || "General")}</div>
        <div>${escapeHtml(n.text)}</div>`;
      list.appendChild(div);
    });
  }

  function renderGarden() {
    const today = L.todayISO();
    const goalStreak = L.goalStreak(state, today);
    const trees = L.treeCount(goalStreak);
    const info = L.stageInfo(state.gardenXp || 0);
    $("#garden-emoji").textContent = info.current.emoji;
    $("#garden-stage").textContent = info.current.name;
    $("#garden-xp").textContent = `${state.gardenXp || 0} XP`;
    $("#garden-trees").textContent = `${trees} trees`;
    $("#garden-goal-streak").textContent = `${goalStreak} complete-day streak`;
    const pct = Math.round((info.progress || 0) * 100);
    $("#garden-progress").style.width = `${pct}%`;
    $("#garden-next").textContent = info.next
      ? `${info.xpToNext} XP to ${info.next.emoji} ${info.next.name}`
      : "Max stage reached";

    const feed = $("#garden-feed");
    feed.innerHTML = "";
    (state.gardenEvents || []).slice(0, 12).forEach((e) => {
      const div = document.createElement("div");
      div.className = "list-note";
      div.innerHTML = `<div class="meta">${escapeHtml(e.date)} · +${e.xp} XP</div><div>${escapeHtml(e.message)}</div>`;
      feed.appendChild(div);
    });
    if (!(state.gardenEvents || []).length) {
      feed.innerHTML = `<p class="muted">Log hours and finish plan items — the garden will grow.</p>`;
    }
  }

  function renderMore() {
    $("#settings-name").value = state.name || "";
    $("#settings-goal").value = state.dailyGoal || 6;
  }

  function render() {
    if (!state) return;
    renderHeader();
    renderWelcome();
    if (page === "today") renderToday();
    if (page === "hours") renderHours();
    if (page === "notes") renderNotes();
    if (page === "garden") renderGarden();
    if (page === "more") renderMore();
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function addHours(amount) {
    const today = L.todayISO();
    const cur = state.hours[today] || { hours: 0, notes: "" };
    cur.hours = Math.round((Number(cur.hours) + amount) * 100) / 100;
    state.hours[today] = cur;
    L.awardHours(state, amount, today);
    await persist();
    toast(`+${amount}h saved · today ${cur.hours}h`);
    render();
  }

  function bind() {
    document.querySelectorAll(".nav button").forEach((btn) => {
      btn.addEventListener("click", () => setPage(btn.dataset.page));
    });

    $("#btn-settings").addEventListener("click", () => {
      setPage("more");
    });

    $("#welcome-ok").addEventListener("click", async () => {
      state.welcomeSeen = true;
      await persist();
      render();
    });

    $("#btn-add-item").addEventListener("click", () => {
      $("#new-item-text").value = "";
      openSheet("#sheet-add-item");
      setTimeout(() => $("#new-item-text").focus(), 200);
    });

    $("#save-item").addEventListener("click", async () => {
      const text = $("#new-item-text").value.trim();
      if (!text) {
        toast("Write something first");
        return;
      }
      const today = L.todayISO();
      const plan = planFor(today);
      plan.items.push({ id: L.uid(), text, status: "Pending" });
      await persist();
      closeSheets();
      toast("Added to today's plan");
      render();
    });

    document.querySelectorAll("[data-add-hours]").forEach((btn) => {
      btn.addEventListener("click", () => addHours(Number(btn.dataset.addHours)));
    });

    $("#save-note").addEventListener("click", async () => {
      const text = $("#note-text").value.trim();
      if (!text) {
        toast("Write a short note");
        return;
      }
      const subject = $("#note-subject").value || "General";
      state.notes.unshift({
        id: L.uid(),
        date: L.todayISO(),
        text,
        subject,
      });
      state.notes = state.notes.slice(0, 500);
      $("#note-text").value = "";
      await persist();
      toast("Note saved");
      render();
    });

    $("#save-settings").addEventListener("click", async () => {
      state.name = ($("#settings-name").value || "Student").trim().slice(0, 40);
      const g = Number($("#settings-goal").value);
      state.dailyGoal = !Number.isFinite(g) || g < 0.5 ? 6 : Math.min(16, g);
      await persist();
      toast("Settings saved");
      render();
    });

    $("#btn-export").addEventListener("click", () => {
      const blob = new Blob([exportJson(state)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `study-tracker-backup-${L.todayISO()}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      toast("Backup downloaded");
    });

    $("#import-file").addEventListener("change", async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        state = importJson(text);
        await persist();
        toast("Backup restored");
        render();
      } catch {
        toast("Could not read that file");
      }
      e.target.value = "";
    });

    $("#sheet-backdrop").addEventListener("click", closeSheets);
    document.querySelectorAll("[data-close-sheet]").forEach((b) =>
      b.addEventListener("click", closeSheets)
    );

    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      deferredInstall = e;
      $("#install-banner").classList.add("show");
    });

    $("#btn-install").addEventListener("click", async () => {
      if (deferredInstall) {
        deferredInstall.prompt();
        const choice = await deferredInstall.userChoice;
        if (choice.outcome === "accepted") toast("Installed on this tablet");
        deferredInstall = null;
        $("#install-banner").classList.remove("show");
      } else {
        toast("Use browser menu → Add to Home screen");
      }
    });

    $("#btn-install-help").addEventListener("click", () => {
      openSheet("#sheet-install-help");
    });
  }

  async function boot() {
    state = await loadState();
    const rewards = L.processCheckin(state);
    if (rewards.length) await persist();
    bind();
    setPage("today");
    if (rewards.length) toast("Welcome back · garden check-in");

    if ("serviceWorker" in navigator) {
      try {
        const swUrl = new URL("sw.js", window.location.href);
        await navigator.serviceWorker.register(swUrl.href, {
          scope: new URL("./", window.location.href).pathname,
        });
      } catch {
        /* offline SW optional when opened as file:// */
      }
    }
  }

  boot();
})();
