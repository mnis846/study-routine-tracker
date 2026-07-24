/**
 * Study rules: streaks, XP, garden growth (mirrors core Streamlit logic, simplified).
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
  const MAX_TREES = 77;

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
    for (let i = 0; i < 400; i++) {
      if (hoursOn(state, cursor) >= goal) {
        streak += 1;
        cursor = addDays(cursor, -1);
      } else break;
    }
    return streak;
  }

  function studyStreak(state, today = todayISO()) {
    // Any hours > 0 counts for "show up" streak
    let cursor = today;
    if (hoursOn(state, today) <= 0) cursor = addDays(today, -1);
    let streak = 0;
    for (let i = 0; i < 400; i++) {
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
    return { index: idx, current, next, progress: Math.min(1, Math.max(0, progress)), xpToNext };
  }

  function treeCount(goalStreakDays) {
    if (goalStreakDays < STREAK_DAYS_PER_TREE) return 1;
    return Math.min(MAX_TREES, 1 + Math.floor(goalStreakDays / STREAK_DAYS_PER_TREE));
  }

  function addXp(state, amount, message) {
    const xp = Math.max(0, Math.floor(amount));
    if (!xp) return null;
    state.gardenXp = (state.gardenXp || 0) + xp;
    const event = { id: uid(), date: todayISO(), xp, message };
    state.gardenEvents = [event, ...(state.gardenEvents || [])].slice(0, 80);
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
      const h = hoursOn(state, d);
      rows.push({ date: d, hours: h, isToday: d === today });
    }
    return rows;
  }

  function heatmapDays(state, days = 119, today = todayISO()) {
    const goal = Number(state.dailyGoal) || 6;
    const out = [];
    for (let i = days - 1; i >= 0; i--) {
      const d = addDays(today, -i);
      const h = hoursOn(state, d);
      out.push({ date: d, hours: h, level: heatLevel(h, goal), isToday: d === today });
    }
    return out;
  }

  global.SRTLogic = {
    XP,
    STAGES,
    todayISO,
    addDays,
    uid,
    hoursOn,
    goalStreak,
    studyStreak,
    stageInfo,
    treeCount,
    processCheckin,
    awardHours,
    awardTargetDone,
    awardAllTargets,
    weekHours,
    heatmapDays,
    heatLevel,
  };
})(window);
