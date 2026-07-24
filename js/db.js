/**
 * Local-first store — designed for 1–2+ years of daily study data on-device.
 * IndexedDB is primary (large quota). localStorage is a compact safety mirror.
 */
(function (global) {
  const DB_NAME = "study-routine-tracker-tablet";
  const DB_VERSION = 2;
  const STORE = "kv";
  const KEY = "app_state_v2";
  const LEGACY_KEYS = ["srt_tablet_state_v1", "app_state_v1"];

  // Retention targets (keep more than a year)
  const KEEP_HOUR_DAYS = 800; // ~2.2 years of daily hours
  const KEEP_PLAN_DAYS = 800;
  const MAX_NOTES = 3000; // ~ multi-year notes
  const MAX_GARDEN_EVENTS = 600;
  const MAX_BONUS_KEYS = 400;

  function defaultState() {
    return {
      version: 2,
      name: "Student",
      dailyGoal: 6,
      hours: {},
      plans: {},
      notes: [],
      gardenXp: 0,
      gardenEvents: [],
      bonuses: {},
      harvestTier: null,
      welcomeSeen: false,
      createdAt: new Date().toISOString(),
      lastSavedAt: null,
    };
  }

  function openIdb() {
    return new Promise((resolve) => {
      if (!global.indexedDB) {
        resolve(null);
        return;
      }
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE);
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    });
  }

  async function idbGet(db, key) {
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE, "readonly");
        const req = tx.objectStore(STORE).get(key);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      } catch {
        resolve(null);
      }
    });
  }

  async function idbSet(db, key, value) {
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).put(value, key);
        tx.oncomplete = () => resolve(true);
        tx.onerror = () => resolve(false);
      } catch {
        resolve(false);
      }
    });
  }

  function loadLegacy() {
    for (const k of LEGACY_KEYS) {
      try {
        const raw = localStorage.getItem(k);
        if (raw) return JSON.parse(raw);
      } catch {
        /* continue */
      }
    }
    // Also try old IDB key via sync path handled in loadState
    return null;
  }

  function compactForLocalStorage(state) {
    // Smaller mirror so we never blow the 5MB localStorage cap
    const hours = {};
    const planKeys = Object.keys(state.plans || {}).sort().slice(-400);
    const hourKeys = Object.keys(state.hours || {}).sort().slice(-400);
    for (const k of hourKeys) hours[k] = state.hours[k];
    const plans = {};
    for (const k of planKeys) plans[k] = state.plans[k];
    return {
      version: state.version,
      name: state.name,
      dailyGoal: state.dailyGoal,
      hours,
      plans,
      notes: (state.notes || []).slice(0, 200),
      gardenXp: state.gardenXp,
      gardenEvents: (state.gardenEvents || []).slice(0, 40),
      bonuses: state.bonuses,
      harvestTier: state.harvestTier,
      welcomeSeen: state.welcomeSeen,
      createdAt: state.createdAt,
      lastSavedAt: state.lastSavedAt,
      _mirror: true,
    };
  }

  function saveLegacy(state) {
    try {
      localStorage.setItem("srt_tablet_state_v2", JSON.stringify(compactForLocalStorage(state)));
      return true;
    } catch {
      try {
        // Drop notes from mirror if still too large
        const tiny = compactForLocalStorage(state);
        tiny.notes = (tiny.notes || []).slice(0, 50);
        localStorage.setItem("srt_tablet_state_v2", JSON.stringify(tiny));
        return true;
      } catch {
        return false;
      }
    }
  }

  function pruneState(state) {
    const today = new Date();
    const cutoff = new Date(today);
    cutoff.setDate(cutoff.getDate() - KEEP_HOUR_DAYS);
    const cutoffISO = cutoff.toISOString().slice(0, 10);

    const hours = {};
    Object.keys(state.hours || {}).forEach((d) => {
      if (d >= cutoffISO) hours[d] = state.hours[d];
    });

    const plans = {};
    Object.keys(state.plans || {}).forEach((d) => {
      if (d >= cutoffISO) plans[d] = state.plans[d];
    });

    // Bonus keys are short-lived; keep recent only
    const bonuses = {};
    const bEntries = Object.entries(state.bonuses || {});
    bEntries
      .sort((a, b) => String(b[1]).localeCompare(String(a[1])))
      .slice(0, MAX_BONUS_KEYS)
      .forEach(([k, v]) => {
        bonuses[k] = v;
      });

    return {
      ...state,
      version: 2,
      hours,
      plans,
      notes: (state.notes || []).slice(0, MAX_NOTES),
      gardenEvents: (state.gardenEvents || []).slice(0, MAX_GARDEN_EVENTS),
      bonuses,
      lastSavedAt: new Date().toISOString(),
    };
  }

  function stats(state) {
    const hourDays = Object.keys(state.hours || {}).length;
    const planDays = Object.keys(state.plans || {}).length;
    const notes = (state.notes || []).length;
    const events = (state.gardenEvents || []).length;
    const payload = JSON.stringify(state);
    return {
      hourDays,
      planDays,
      notes,
      events,
      approxBytes: payload.length,
      approxKB: Math.round(payload.length / 1024),
      retentionDays: KEEP_HOUR_DAYS,
    };
  }

  async function loadState() {
    const base = defaultState();
    let data = null;
    const db = await openIdb();
    if (db) {
      data = (await idbGet(db, KEY)) || (await idbGet(db, "app_state_v1"));
      db.close();
    }
    if (!data) {
      try {
        const raw = localStorage.getItem("srt_tablet_state_v2");
        if (raw) data = JSON.parse(raw);
      } catch {
        /* ignore */
      }
    }
    if (!data) data = loadLegacy();
    if (!data) return base;
    const merged = { ...base, ...data, version: 2 };
    if (!merged.createdAt) merged.createdAt = base.createdAt;
    return pruneState(merged);
  }

  async function saveState(state) {
    const payload = pruneState(state);
    let ok = false;
    const db = await openIdb();
    if (db) {
      ok = await idbSet(db, KEY, payload);
      db.close();
    }
    saveLegacy(payload);
    return ok || true;
  }

  function exportJson(state) {
    return JSON.stringify(pruneState(state), null, 2);
  }

  function importJson(text) {
    const data = JSON.parse(text);
    if (!data || typeof data !== "object") throw new Error("Invalid backup file");
    return pruneState({ ...defaultState(), ...data, version: 2 });
  }

  global.SRTDB = {
    defaultState,
    loadState,
    saveState,
    exportJson,
    importJson,
    pruneState,
    stats,
    KEEP_HOUR_DAYS,
    MAX_NOTES,
  };
})(window);
