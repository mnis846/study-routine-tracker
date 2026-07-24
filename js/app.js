(function () {
  const { loadState, saveState, exportJson, importJson, stats } = window.SRTDB;
  const L = window.SRTLogic;

  let state = null;
  let page = "today";
  let deferredInstall = null;
  let gardenCtrl = null;
  let editHoursDate = null;
  let editNoteId = null;
  let editItemId = null;

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
    if (name === "garden" && gardenCtrl) {
      gardenCtrl.start();
      requestAnimationFrame(() => gardenCtrl.layout());
    } else if (gardenCtrl) {
      gardenCtrl.stop();
    }
    render();
    window.scrollTo(0, 0);
    // Scroll heatmap to show recent weeks (right side)
    if (name === "hours") {
      requestAnimationFrame(() => {
        const sc = $("#heat-scroll");
        if (sc) sc.scrollLeft = sc.scrollWidth;
      });
    }
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
    const todayH = L.hoursOn(state, today);
    const goal = Number(state.dailyGoal) || 6;
    const goalLabel = Number.isInteger(goal) ? String(goal) : String(goal);
    $("#stat-streak").textContent = String(streak);
    $("#stat-goal").textContent = `${goalLabel}h`;
    $("#stat-today").textContent = `${todayH}h`;
    $("#stat-xp").textContent = String(state.gardenXp || 0);
    const treesEl = $("#stat-trees");
    if (treesEl) treesEl.textContent = String(L.treeCount(L.goalStreak(state, today)));
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
          <div class="btn-row" style="margin-top:8px;grid-template-columns:1fr 1fr">
            <button class="ghost" data-act="edit">Edit</button>
            ${
              item.status === "Skipped"
                ? `<button class="ghost" data-act="unskip">Undo skip</button>`
                : item.status === "Done"
                  ? `<button class="ghost" data-act="undone">Undo done</button>`
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
      div.querySelector('[data-act="undone"]')?.addEventListener("click", async () => {
        item.status = "Pending";
        await persist();
        toast("Marked as not done");
        render();
      });
      div.querySelector('[data-act="edit"]')?.addEventListener("click", () => {
        openEditItem(item.id);
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
    const maxDay = L.MAX_DAILY_HOURS || 10;
    const todayH = L.hoursOn(state, today);
    const pct = Math.min(100, Math.round((todayH / goal) * 100));
    $("#hours-today").textContent = `${todayH}h / ${goal}h goal (max ${maxDay}h)`;
    $("#hours-progress").style.width = `${pct}%`;

    // Disable add buttons near cap
    document.querySelectorAll("[data-add-hours]").forEach((btn) => {
      const add = Number(btn.dataset.addHours);
      btn.disabled = todayH >= maxDay || todayH + add > maxDay + 0.001;
      btn.style.opacity = btn.disabled ? "0.45" : "1";
    });
    document.querySelectorAll("[data-sub-hours]").forEach((btn) => {
      btn.disabled = todayH <= 0;
      btn.style.opacity = btn.disabled ? "0.45" : "1";
    });

    const week = L.weekHours(state, today);
    const maxH = Math.max(goal, ...week.map((w) => w.hours), 1);
    const bars = $("#week-bars");
    bars.innerHTML = "";
    week.forEach((w) => {
      const h = Math.max(4, Math.round((w.hours / maxH) * 100));
      const label = new Date(w.date + "T12:00:00").toLocaleDateString(undefined, {
        weekday: "short",
      });
      const wrap = document.createElement("div");
      wrap.className = "bar-wrap";
      wrap.innerHTML = `<div class="bar ${w.isToday ? "today" : ""}" style="height:${w.hours ? h : 4}%"></div><span class="dlabel">${label}</span>`;
      bars.appendChild(wrap);
    });

    // Recent days list (editable)
    const recent = $("#recent-hours-list");
    if (recent) {
      const days = Object.keys(state.hours || {})
        .sort()
        .reverse()
        .slice(0, 21);
      if (!days.length) {
        recent.innerHTML = `<p class="muted">No hours logged yet.</p>`;
      } else {
        recent.innerHTML = "";
        days.forEach((d) => {
          const h = L.hoursOn(state, d);
          const notes = state.hours[d]?.notes || "";
          const row = document.createElement("div");
          row.className = "list-note recent-hour-row";
          row.innerHTML = `
            <div class="meta">${escapeHtml(d)}${d === today ? " · today" : ""}</div>
            <div><strong>${h}h</strong>${notes ? ` · ${escapeHtml(notes)}` : ""}</div>
            <button class="ghost" type="button" style="margin-top:6px;min-height:40px">Edit / fix</button>`;
          row.querySelector("button").addEventListener("click", () => openEditHours(d));
          recent.appendChild(row);
        });
      }
    }

    renderHeatmap(today);
  }

  function renderHeatmap(today) {
    const grid = L.heatmapGrid(state, today);
    const heat = $("#heatmap");
    const months = $("#heat-months");
    if (!heat) return;

    $("#heat-summary").textContent =
      `${grid.showups} days shown · ${grid.totalHours}h in the last year`;

    months.innerHTML = "";
    grid.monthLabels.forEach((lbl) => {
      const s = document.createElement("span");
      s.textContent = lbl || "";
      months.appendChild(s);
    });

    heat.innerHTML = "";
    grid.weeks.forEach((week) => {
      week.forEach((c) => {
        const i = document.createElement("i");
        if (c.isFuture || c.level < 0) i.className = "future";
        else i.className = `l${c.level}`;
        if (c.isToday) i.classList.add("today");
        const tip =
          c.isFuture
            ? c.date
            : c.hours > 0
              ? `${c.date}: ${c.hours}h`
              : `${c.date}: no study`;
        i.title = tip;
        i.setAttribute("aria-label", tip);
        i.addEventListener("click", () => {
          $("#heat-tip").textContent = tip + (c.isFuture ? "" : " · tap Edit below to change");
          if (!c.isFuture) openEditHours(c.date);
        });
        heat.appendChild(i);
      });
    });

    requestAnimationFrame(() => {
      const sc = $("#heat-scroll");
      if (sc) sc.scrollLeft = sc.scrollWidth;
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
        <div>${escapeHtml(n.text)}</div>
        <button class="ghost" type="button" style="margin-top:6px;min-height:40px">Edit / delete</button>`;
      div.querySelector("button").addEventListener("click", () => openEditNote(n.id));
      list.appendChild(div);
    });
  }

  function openEditHours(dateStr) {
    editHoursDate = dateStr;
    const h = L.hoursOn(state, dateStr);
    const notes = state.hours[dateStr]?.notes || "";
    $("#edit-hours-title").textContent = "Edit hours";
    $("#edit-hours-date").textContent = dateStr;
    $("#edit-hours-value").value = h;
    $("#edit-hours-value").max = L.MAX_DAILY_HOURS || 10;
    $("#edit-hours-notes").value = notes;
    openSheet("#sheet-edit-hours");
  }

  function openEditNote(id) {
    const n = (state.notes || []).find((x) => x.id === id);
    if (!n) return;
    editNoteId = id;
    $("#edit-note-text").value = n.text || "";
    const sel = $("#edit-note-subject");
    const sub = n.subject || "General";
    // ensure option exists
    let found = false;
    for (const opt of sel.options) {
      if (opt.value === sub || opt.text === sub) {
        sel.value = opt.value;
        found = true;
        break;
      }
    }
    if (!found) {
      const o = document.createElement("option");
      o.text = sub;
      o.value = sub;
      sel.add(o);
      sel.value = sub;
    }
    openSheet("#sheet-edit-note");
  }

  function openEditItem(id) {
    const today = L.todayISO();
    const item = planFor(today).items.find((x) => x.id === id);
    if (!item) return;
    editItemId = id;
    $("#edit-item-text").value = item.text || "";
    openSheet("#sheet-edit-item");
  }

  function renderGarden() {
    const today = L.todayISO();
    const life = L.gardenLife(state, today);
    const info = life.stage || L.stageInfo(state.gardenXp || 0);

    if (gardenCtrl) {
      gardenCtrl.setLife(life);
      gardenCtrl.start();
    }

    $("#garden-emoji").textContent = info.current.emoji;
    $("#garden-stage").textContent = info.current.name;
    $("#garden-xp").textContent = `${state.gardenXp || 0} XP`;
    $("#garden-trees").textContent = `${life.tree_count} trees`;
    $("#garden-goal-streak").textContent =
      `${life.goal_streak} complete-day streak · ${life.mood}`;
    const pct = Math.round((info.progress || 0) * 100);
    $("#garden-progress").style.width = `${pct}%`;
    $("#garden-next").textContent = info.next
      ? `${info.xpToNext} XP to ${info.next.emoji} ${info.next.name}`
      : "Max evolution stage reached";
    $("#garden-hint").textContent = life.hint || "";
    $("#garden-life").textContent = `${life.life}`;
    $("#garden-water").textContent = `${life.water_pct}%`;
    $("#garden-harvest").textContent = `${life.harvest_emoji}`;
    $("#garden-foundation").textContent =
      `${life.foundation_trees}/${life.foundation_target}`;

    // week vitality dots
    const dots = $("#garden-week-dots");
    if (dots) {
      dots.innerHTML =
        '<span class="muted" style="font-size:0.78rem;font-weight:600;margin-right:4px">This week</span>';
      (life.week_days || []).forEach((d) => {
        const s = document.createElement("span");
        s.className = `week-dot ${d.status}`;
        s.title = `${d.date}: ${d.hours}h`;
        dots.appendChild(s);
      });
    }

    // evolution badges
    const badges = $("#garden-badges");
    if (badges) {
      badges.innerHTML = "";
      L.STAGES.forEach((stage, i) => {
        const earned = (state.gardenXp || 0) >= stage.min_xp;
        const span = document.createElement("span");
        span.className = `badge ${earned ? "earned" : "locked"}`;
        span.textContent = `${stage.emoji} ${stage.name}${earned ? "" : " 🔒"}`;
        badges.appendChild(span);
      });
    }

    // latest trees list
    const list = $("#garden-tree-list");
    if (list) {
      const trees = life.trees || [];
      const show = trees.slice(-8);
      if (!show.length) {
        list.innerHTML = `<p class="muted">Log ${life.daily_goal}h days to plant trees.</p>`;
      } else {
        list.innerHTML = show
          .map((tr) => {
            const fruit = tr.has_fruit ? "🍎 Fruit" : "🌿 Growing";
            return `<div class="tree-row"><strong>#${tr.tree_no}</strong> · ${escapeHtml(tr.phase)} · ${escapeHtml(tr.subject)} · ${fruit}</div>`;
          })
          .join("");
        if (trees.length > 8) {
          list.innerHTML += `<p class="muted">Showing latest 8 of ${trees.length} — swipe the map for all.</p>`;
        }
      }
    }

    const feed = $("#garden-feed");
    feed.innerHTML = "";
    (state.gardenEvents || []).slice(0, 15).forEach((e) => {
      const div = document.createElement("div");
      div.className = "list-note";
      div.innerHTML = `<div class="meta">${escapeHtml(e.date)} · +${e.xp} XP</div><div>${escapeHtml(e.message)}</div>`;
      feed.appendChild(div);
    });
    if (!(state.gardenEvents || []).length) {
      feed.innerHTML =
        `<p class="muted">Log hours and finish plan items — the garden will grow.</p>`;
    }

    const treesEl = $("#stat-trees");
    if (treesEl) treesEl.textContent = String(life.tree_count);
  }

  function renderMore() {
    $("#settings-name").value = state.name || "";
    $("#settings-goal").value = state.dailyGoal || 6;
    const s = stats(state);
    const el = $("#storage-stats");
    if (el) {
      el.textContent =
        `${s.hourDays} days with hours · ${s.planDays} plan days · ` +
        `${s.notes} notes · ${s.events} garden events · ~${s.approxKB} KB ` +
        `(keeps ~${Math.round(s.retentionDays / 365 * 10) / 10} years)`;
    }
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
    const prev = L.hoursOn(state, today);
    const maxDay = L.MAX_DAILY_HOURS || 10;
    if (prev >= maxDay) {
      toast(`Daily max is ${maxDay}h`);
      return;
    }
    const result = L.addHoursClamped(state, amount, today);
    if (result.applied === prev) {
      toast(`Can't go over ${maxDay}h today`);
      return;
    }
    await persist();
    toast(`+${result.delta}h · today ${result.applied}h / ${maxDay}h max`);
    render();
  }

  async function subHours(amount) {
    const today = L.todayISO();
    const prev = L.hoursOn(state, today);
    if (prev <= 0) {
      toast("Nothing to remove today");
      return;
    }
    const result = L.addHoursClamped(state, -Math.abs(amount), today);
    await persist();
    toast(
      result.applied <= 0
        ? "Today cleared"
        : `−${Math.abs(result.delta)}h · today ${result.applied}h`
    );
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
    document.querySelectorAll("[data-sub-hours]").forEach((btn) => {
      btn.addEventListener("click", () => subHours(Number(btn.dataset.subHours)));
    });

    $("#btn-edit-today-hours")?.addEventListener("click", () => {
      openEditHours(L.todayISO());
    });
    $("#btn-clear-today-hours")?.addEventListener("click", async () => {
      const today = L.todayISO();
      if (L.hoursOn(state, today) <= 0) {
        toast("Today is already empty");
        return;
      }
      if (!confirm("Clear all hours for today?")) return;
      L.setDayHours(state, today, 0);
      await persist();
      toast("Today cleared");
      render();
    });

    $("#edit-hours-save")?.addEventListener("click", async () => {
      if (!editHoursDate) return;
      let val = Number($("#edit-hours-value").value);
      if (!Number.isFinite(val) || val < 0) val = 0;
      const maxDay = L.MAX_DAILY_HOURS || 10;
      if (val > maxDay) {
        toast(`Max is ${maxDay}h per day`);
        val = maxDay;
      }
      const notes = ($("#edit-hours-notes").value || "").trim();
      const result = L.setDayHours(state, editHoursDate, val);
      if (result.applied > 0) {
        state.hours[editHoursDate].notes = notes;
      }
      await persist();
      closeSheets();
      toast(
        result.applied <= 0
          ? `${editHoursDate} cleared`
          : `${editHoursDate} set to ${result.applied}h`
      );
      editHoursDate = null;
      render();
    });

    $("#edit-hours-clear")?.addEventListener("click", async () => {
      if (!editHoursDate) return;
      L.setDayHours(state, editHoursDate, 0);
      await persist();
      closeSheets();
      toast(`${editHoursDate} cleared`);
      editHoursDate = null;
      render();
    });

    $("#edit-note-save")?.addEventListener("click", async () => {
      if (!editNoteId) return;
      const n = (state.notes || []).find((x) => x.id === editNoteId);
      if (!n) return;
      const text = ($("#edit-note-text").value || "").trim();
      if (!text) {
        toast("Note can't be empty");
        return;
      }
      n.text = text;
      n.subject = $("#edit-note-subject").value || "General";
      await persist();
      closeSheets();
      toast("Note updated");
      editNoteId = null;
      render();
    });

    $("#edit-note-delete")?.addEventListener("click", async () => {
      if (!editNoteId) return;
      if (!confirm("Delete this note?")) return;
      state.notes = (state.notes || []).filter((x) => x.id !== editNoteId);
      await persist();
      closeSheets();
      toast("Note deleted");
      editNoteId = null;
      render();
    });

    $("#edit-item-save")?.addEventListener("click", async () => {
      if (!editItemId) return;
      const today = L.todayISO();
      const item = planFor(today).items.find((x) => x.id === editItemId);
      if (!item) return;
      const text = ($("#edit-item-text").value || "").trim();
      if (!text) {
        toast("Write something first");
        return;
      }
      item.text = text;
      await persist();
      closeSheets();
      toast("Plan item updated");
      editItemId = null;
      render();
    });

    $("#edit-item-delete")?.addEventListener("click", async () => {
      if (!editItemId) return;
      if (!confirm("Delete this plan item?")) return;
      const today = L.todayISO();
      const plan = planFor(today);
      plan.items = plan.items.filter((x) => x.id !== editItemId);
      await persist();
      closeSheets();
      toast("Plan item deleted");
      editItemId = null;
      render();
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
      state.notes = state.notes.slice(0, 3000);
      $("#note-text").value = "";
      await persist();
      toast("Note saved");
      render();
    });

    $("#save-settings").addEventListener("click", async () => {
      state.name = ($("#settings-name").value || "Student").trim().slice(0, 40);
      const g = Number($("#settings-goal").value);
      const maxDay = L.MAX_DAILY_HOURS || 10;
      state.dailyGoal =
        !Number.isFinite(g) || g < 0.5 ? 6 : Math.min(maxDay, g);
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
        const hourDays = Object.keys(state.hours || {}).length;
        const totalH = Object.values(state.hours || {}).reduce(
          (s, v) => s + Number(v?.hours || 0),
          0
        );
        toast(
          `Restored · ${hourDays} day(s) · ${Math.round(totalH * 10) / 10}h · ${state.gardenXp || 0} XP`
        );
        render();
      } catch {
        toast("Could not read that file — use the Android JSON export");
      }
      e.target.value = "";
    });

    $("#sheet-backdrop").addEventListener("click", closeSheets);
    document.querySelectorAll("[data-close-sheet]").forEach((b) =>
      b.addEventListener("click", closeSheets)
    );

    // Chrome may or may not fire this — never rely on it alone.
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      deferredInstall = e;
      $("#install-banner")?.classList.add("show");
    });

    $("#btn-install")?.addEventListener("click", async () => {
      if (deferredInstall) {
        deferredInstall.prompt();
        const choice = await deferredInstall.userChoice;
        if (choice.outcome === "accepted") {
          toast("Added to home screen");
          localStorage.setItem("srt_install_dismissed", "1");
          $("#install-banner")?.classList.remove("show");
        }
        deferredInstall = null;
      } else {
        openSheet("#sheet-install-help");
      }
    });

    $("#btn-install-help")?.addEventListener("click", () => {
      openSheet("#sheet-install-help");
    });

    $("#btn-dismiss-install")?.addEventListener("click", () => {
      localStorage.setItem("srt_install_dismissed", "1");
      $("#install-banner")?.classList.remove("show");
    });
  }

  function isStandalone() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true ||
      document.documentElement.getAttribute("data-packaged") === "capacitor"
    );
  }

  async function boot() {
    if (isStandalone()) {
      document.documentElement.classList.add("standalone");
    } else if (localStorage.getItem("srt_install_dismissed") === "1") {
      $("#install-banner")?.classList.remove("show");
    } else {
      $("#install-banner")?.classList.add("show");
    }

    const canvas = $("#garden-canvas");
    if (canvas && window.SRTGarden) {
      gardenCtrl = window.SRTGarden.createGarden(canvas);
    }

    state = await loadState();
    const rewards = L.processCheckin(state);
    if (rewards.length) await persist();
    bind();
    setPage("today");
    if (rewards.length) toast("Welcome back · garden check-in");

    // Service worker only helps on a real HTTPS origin (e.g. GitHub Pages).
    // CDNs often break installability — APK is the reliable path.
    if ("serviceWorker" in navigator && !isStandalone()) {
      try {
        const baseEl = document.querySelector("base");
        const baseHref = baseEl?.href || window.location.href;
        const swUrl = new URL("sw.js", baseHref);
        await navigator.serviceWorker.register(swUrl.href, {
          scope: new URL("./", baseHref).pathname,
        });
      } catch {
        /* optional */
      }
    }
  }

  boot();
})();
