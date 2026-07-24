/**
 * Study rules: streaks, XP, garden grove, year-long heatmap.
 */
(function (global) {
  const XP = {
    daily_checkin: 25,
    per_hour: 30,
    target_done: 25,
    all_targets: 100,
    daily_goal: 75,
    streak_per_day: 8,
    streak_cap: 60,
  };

  const STAGES = [
    { name: "Barren Plot", min_xp: 0, emoji: "🏚️" },
    { name: "Ash Soil", min_xp: 30, emoji: "🪨" },
    { name: "First Sprout", min_xp: 80, emoji: "🌱" },
    { name: "Scrubland", min_xp: 150, emoji: "🌿" },
    { name: "Trail Cleared", min_xp: 250, emoji: "🥾" },
    { name: "Campfire Ring", min_xp: 400, emoji: "🔥" },
    { name: "Fence Line", min_xp: 600, emoji: "🪵" },
    { name: "Small Outpost", min_xp: 850, emoji: "🏕️" },
    { name: "Water Tank", min_xp: 1150, emoji: "💧" },
    { name: "Green Patch", min_xp: 1500, emoji: "🌳" },
    { name: "Pine Belt", min_xp: 1900, emoji: "🌲" },
    { name: "Supply Yard", min_xp: 2400, emoji: "📦" },
    { name: "Reinforced Base", min_xp: 3000, emoji: "🛡️" },
    { name: "Berry Thicket", min_xp: 3700, emoji: "🫐" },
    { name: "Overgrown Wall", min_xp: 4500, emoji: "🌴" },
    { name: "Wild Perimeter", min_xp: 5400, emoji: "🦌" },
    { name: "Reclaimed Sector", min_xp: 6500, emoji: "🦜" },
    { name: "Apex Haven", min_xp: 8000, emoji: "🏆" },
  ];

  const STREAK_DAYS_PER_TREE = 4;
  const FOUNDATION_TREE_TARGET = 55;
  const MAX_TREES = 77;
  /** Hard cap — realistic max study hours per calendar day */
  const MAX_DAILY_HOURS = 10;

  const HARVEST_TIERS = [
    { id: "sprout", min_days: 0, emoji: "🌱", label: "First Tree" },
    { id: "grove", min_days: 4, emoji: "🌳", label: "Second Tree" },
    { id: "fruit", min_days: 6, emoji: "🍎", label: "Fruit Season" },
    { id: "golden", min_days: 7, emoji: "🏆", label: "Golden Grove" },
  ];

  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function todayISO(d = new Date()) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function parseISO(s) {
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d);
  }

  function addDays(iso, n) {
    const d = parseISO(iso);
    d.setDate(d.getDate() + n);
    return todayISO(d);
  }

  function uid() {
    return `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function hoursOn(state, date) {
    return Number(state.hours[date]?.hours || 0);
  }

  function goalStreak(state, today = todayISO()) {
    const goal = Number(state.dailyGoal) || 6;
    let cursor = today;
    if (hoursOn(state, today) < goal) cursor = addDays(today, -1);
    let streak = 0;
    for (let i = 0; i < 800; i++) {
      if (hoursOn(state, cursor) >= goal) {
        streak += 1;
        cursor = addDays(cursor, -1);
      } else break;
    }
    return streak;
  }

  function studyStreak(state, today = todayISO()) {
    let cursor = today;
    if (hoursOn(state, today) <= 0) cursor = addDays(today, -1);
    let streak = 0;
    for (let i = 0; i < 800; i++) {
      if (hoursOn(state, cursor) > 0) {
        streak += 1;
        cursor = addDays(cursor, -1);
      } else break;
    }
    return streak;
  }

  function heatLevel(hours, goal) {
    if (hours <= 0) return 0;
    if (hours >= goal) return 4;
    if (hours >= goal * 0.5) return 3;
    if (hours >= 1) return 2;
    return 1;
  }

  function stageInfo(xp) {
    let idx = 0;
    for (let i = 0; i < STAGES.length; i++) {
      if (xp >= STAGES[i].min_xp) idx = i;
    }
    const current = STAGES[idx];
    const next = STAGES[idx + 1] || null;
    let progress = 1;
    let xpToNext = 0;
    if (next) {
      const span = next.min_xp - current.min_xp;
      progress = span ? (xp - current.min_xp) / span : 1;
      xpToNext = Math.max(0, next.min_xp - xp);
    }
    return {
      index: idx,
      current,
      next,
      progress: Math.min(1, Math.max(0, progress)),
      xpToNext,
    };
  }

  function treeCount(goalStreakDays) {
    if (goalStreakDays < STREAK_DAYS_PER_TREE) return 1;
    return Math.min(MAX_TREES, 1 + Math.floor(goalStreakDays / STREAK_DAYS_PER_TREE));
  }

  function harvestTier(goalStreakDays) {
    let tier = HARVEST_TIERS[0];
    for (const t of HARVEST_TIERS) {
      if (goalStreakDays >= t.min_days) tier = t;
    }
    return tier;
  }

  function weekGoalDays(state, today = todayISO()) {
    const goal = Number(state.dailyGoal) || 6;
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const d = addDays(today, -i);
      const h = hoursOn(state, d);
      let status = "empty";
      if (h >= goal) status = "complete";
      else if (h > 0) status = "partial";
      days.push({ date: d, hours: h, status });
    }
    return days;
  }

  function buildTrees(goalStreakDays, water, hasFruit) {
    const unlocked = treeCount(goalStreakDays);
    const trees = [];
    for (let n = 1; n <= unlocked; n++) {
      const phase = n <= FOUNDATION_TREE_TARGET ? "foundation" : "sprint";
      let growth = "sapling";
      if (goalStreakDays >= 4) growth = "mature";
      else if (goalStreakDays >= 2) growth = "young";
      if (hasFruit) growth = "fruiting";
      trees.push({
        tree_no: n,
        phase,
        subject:
          phase === "foundation"
            ? `Foundation Block ${n}`
            : `Exam Sprint ${n - FOUNDATION_TREE_TARGET}`,
        growth,
        has_fruit: hasFruit,
        water,
      });
    }
    return trees;
  }

  function gardenLife(state, today = todayISO()) {
    const goal = Number(state.dailyGoal) || 6;
    const todayHours = hoursOn(state, today);
    const gStreak = goalStreak(state, today);
    const week = weekGoalDays(state, today);
    const unlocked = treeCount(gStreak);
    const water = goal > 0 ? Math.min(1, todayHours / goal) : 0;
    const hasFruit = gStreak >= 6;
    const trees = buildTrees(gStreak, water, hasFruit);
    const tier = harvestTier(gStreak);
    const foundationTrees = Math.min(unlocked, FOUNDATION_TREE_TARGET);
    const daysToNextTree =
      unlocked < MAX_TREES ? Math.max(0, unlocked * STREAK_DAYS_PER_TREE - gStreak) : 0;

    let life = 28;
    week.forEach((d) => {
      if (d.status === "complete") life += 10;
      else if (d.status === "partial") life += 3;
    });
    life = Math.min(100, life);

    const goalMet = todayHours >= goal;
    let mood = "resting";
    let hint =
      `Long prep path: ~${FOUNDATION_TREE_TARGET} foundation trees + exam sprint. ` +
      `Study ${goal}h/day — 4 complete days plant a new tree.`;
    if (goalMet) {
      mood = "flourishing";
      hint = `${gStreak}-day complete streak · ${unlocked}/${MAX_TREES} trees · foundation ${foundationTrees}/${FOUNDATION_TREE_TARGET}.`;
    } else if (todayHours > 0) {
      mood = "growing";
      hint = `Watering ${Math.round(water * 100)}% — ${(goal - todayHours).toFixed(1)}h more today keeps the grove alive.`;
    } else if (gStreak > 0) {
      mood = "thirsty";
      hint = "Trees are thirsty — log hours before midnight to protect your streak.";
    }
    if (daysToNextTree > 0 && unlocked < MAX_TREES) {
      hint += ` · ${daysToNextTree}d until tree #${unlocked + 1}.`;
    }

    return {
      life,
      mood,
      goal_streak: gStreak,
      harvest_tier: tier.id,
      harvest_label: tier.label,
      harvest_emoji: tier.emoji,
      trees,
      tree_count: unlocked,
      unlocked_count: unlocked,
      max_trees: MAX_TREES,
      foundation_target: FOUNDATION_TREE_TARGET,
      foundation_trees: foundationTrees,
      journey_phase: unlocked <= FOUNDATION_TREE_TARGET ? "foundation" : "sprint",
      has_fruit: hasFruit,
      water_level: water,
      water_pct: Math.round(water * 100),
      today_hours: todayHours,
      daily_goal: goal,
      goal_met: goalMet,
      week_days: week,
      days_to_next_tree: daysToNextTree,
      next_tree:
        unlocked < MAX_TREES
          ? { tree_no: unlocked + 1, days_away: daysToNextTree }
          : null,
      hint,
      stage: stageInfo(state.gardenXp || 0),
    };
  }

  function addXp(state, amount, message) {
    const xp = Math.max(0, Math.floor(amount));
    if (!xp) return null;
    state.gardenXp = (state.gardenXp || 0) + xp;
    const event = { id: uid(), date: todayISO(), xp, message };
    state.gardenEvents = [event, ...(state.gardenEvents || [])].slice(0, 600);
    return event;
  }

  function bonusOnce(state, key, today = todayISO()) {
    if (state.bonuses[key] === today) return false;
    state.bonuses[key] = today;
    return true;
  }

  function processCheckin(state, today = todayISO()) {
    const rewards = [];
    if (bonusOnce(state, "checkin", today)) {
      const streak = studyStreak(state, today);
      rewards.push(addXp(state, XP.daily_checkin, "Daily check-in"));
      const bonus = Math.min(streak * XP.streak_per_day, XP.streak_cap);
      if (bonus > 0) rewards.push(addXp(state, bonus, `Streak bonus (${streak} days)`));
    }
    return rewards.filter(Boolean);
  }

  function clampDailyHours(hours) {
    const n = Number(hours) || 0;
    if (n <= 0) return 0;
    return Math.min(MAX_DAILY_HOURS, Math.round(n * 100) / 100);
  }

  /**
   * Set absolute hours for a date (0 clears the day). Returns { applied, previous, rewards }.
   * XP is only awarded when hours increase (not on corrections downward).
   */
  function setDayHours(state, date, nextHours) {
    const previous = hoursOn(state, date);
    const applied = clampDailyHours(nextHours);
    if (applied <= 0) {
      delete state.hours[date];
    } else {
      const notes = state.hours[date]?.notes || "";
      state.hours[date] = { hours: applied, notes };
    }
    const delta = Math.round((applied - previous) * 100) / 100;
    const rewards = [];
    if (delta > 0) {
      rewards.push(...awardHours(state, delta, date));
    }
    // If they drop below goal after having hit it same day, clear daily_goal bonus flag
    // so re-hitting goal later can award again (optional fairness on corrections).
    const goal = Number(state.dailyGoal) || 6;
    if (previous >= goal && applied < goal && state.bonuses) {
      if (state.bonuses.daily_goal === date) delete state.bonuses.daily_goal;
    }
    return { applied, previous, delta, rewards: rewards.filter(Boolean) };
  }

  function addHoursClamped(state, amount, date = todayISO()) {
    const previous = hoursOn(state, date);
    const target = clampDailyHours(previous + (Number(amount) || 0));
    return setDayHours(state, date, target);
  }

  function awardHours(state, hours, date = todayISO()) {
    const rewards = [];
    const amount = Number(hours) || 0;
    if (amount > 0) {
      rewards.push(addXp(state, amount * XP.per_hour, `Studied ${amount}h`));
    }
    const total = hoursOn(state, date);
    const goal = Number(state.dailyGoal) || 6;
    if (total >= goal && bonusOnce(state, "daily_goal", date)) {
      rewards.push(addXp(state, XP.daily_goal, "Hit daily goal"));
    }
    return rewards.filter(Boolean);
  }

  function awardTargetDone(state) {
    return addXp(state, XP.target_done, "Finished a plan item");
  }

  function awardAllTargets(state, date = todayISO()) {
    if (!bonusOnce(state, "all_targets", date)) return null;
    return addXp(state, XP.all_targets, "All plan items done");
  }

  function weekHours(state, today = todayISO()) {
    const rows = [];
    for (let i = 6; i >= 0; i--) {
      const d = addDays(today, -i);
      rows.push({ date: d, hours: hoursOn(state, d), isToday: d === today });
    }
    return rows;
  }

  /**
   * GitHub-style contribution grid for ~1 year (53 weeks).
   * Columns = weeks (Sun→Sat rows), smooth horizontal scroll in UI.
   */
  function heatmapGrid(state, today = todayISO()) {
    const goal = Number(state.dailyGoal) || 6;
    const end = parseISO(today);
    // Align end week to Saturday for GitHub-style
    const endDow = end.getDay(); // 0 Sun
    // Start: 52 weeks back from start of this week (Sunday)
    const start = new Date(end);
    start.setDate(start.getDate() - endDow - 52 * 7);

    const weeks = [];
    const monthLabels = [];
    let cursor = new Date(start);
    let showups = 0;
    let totalHours = 0;

    for (let w = 0; w < 53; w++) {
      const week = [];
      let monthLabel = "";
      for (let d = 0; d < 7; d++) {
        const iso = todayISO(cursor);
        const future = cursor > end;
        const h = future ? 0 : hoursOn(state, iso);
        if (!future) {
          totalHours += h;
          if (h > 0) showups += 1;
        }
        if (cursor.getDate() === 1) monthLabel = MONTHS[cursor.getMonth()];
        week.push({
          date: iso,
          hours: h,
          level: future ? -1 : heatLevel(h, goal),
          isToday: iso === today,
          isFuture: future,
        });
        cursor.setDate(cursor.getDate() + 1);
      }
      weeks.push(week);
      monthLabels.push(monthLabel);
    }

    return {
      weeks,
      monthLabels,
      showups,
      totalHours: Math.round(totalHours * 10) / 10,
      goal,
    };
  }

  global.SRTLogic = {
    XP,
    STAGES,
    HARVEST_TIERS,
    FOUNDATION_TREE_TARGET,
    MAX_TREES,
    MAX_DAILY_HOURS,
    todayISO,
    parseISO,
    addDays,
    uid,
    hoursOn,
    goalStreak,
    studyStreak,
    stageInfo,
    treeCount,
    gardenLife,
    processCheckin,
    awardHours,
    addHoursClamped,
    setDayHours,
    clampDailyHours,
    awardTargetDone,
    awardAllTargets,
    weekHours,
    heatmapGrid,
    heatLevel,
  };
})(window);
