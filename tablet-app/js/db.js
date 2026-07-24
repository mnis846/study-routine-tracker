/**
 * Local-first store for the tablet app.
 * All study data stays in the browser (IndexedDB when available, localStorage fallback).
 */
(function (global) {
  const DB_NAME = "study-routine-tracker-tablet";
  const STORE = "kv";
  const KEY = "app_state_v1";
  const LEGACY_KEY = "srt_tablet_state_v1";

  function defaultState() {
    return {
      version: 1,
      name: "Student",
      dailyGoal: 6,
      hours: {}, // date -> { hours: number, notes: string }
      plans: {}, // date -> { items: [{ id, text, status }] }
      notes: [], // [{ id, date, text, subject }]
      gardenXp: 0,
      gardenEvents: [], // [{ date, xp, message }]
      bonuses: {}, // key -> date string (once-per-day flags)
      welcomeSeen: false,
    };
  }

  function openIdb() {
    return new Promise((resolve, reject) => {
      if (!global.indexedDB) {
        resolve(null);
        return;
      }
      const req = indexedDB.open(DB_NAME, 1);
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

  async function idbGet(db) {
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE, "readonly");
        const req = tx.objectStore(STORE).get(KEY);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      } catch {
        resolve(null);
      }
    });
  }

  async function idbSet(db, value) {
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).put(value, KEY);
        tx.oncomplete = () => resolve(true);
        tx.onerror = () => resolve(false);
      } catch {
        resolve(false);
      }
    });
  }

  function loadLegacy() {
    try {
      const raw = localStorage.getItem(LEGACY_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function saveLegacy(state) {
    try {
      localStorage.setItem(LEGACY_KEY, JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }

  async function loadState() {
    const base = defaultState();
    let data = null;
    const db = await openIdb();
    if (db) {
      data = await idbGet(db);
      db.close();
    }
    if (!data) data = loadLegacy();
    if (!data) return base;
    return { ...base, ...data, version: 1 };
  }

  async function saveState(state) {
    const payload = { ...state, version: 1 };
    saveLegacy(payload);
    const db = await openIdb();
    if (db) {
      await idbSet(db, payload);
      db.close();
    }
    return true;
  }

  function exportJson(state) {
    return JSON.stringify(state, null, 2);
  }

  function importJson(text) {
    const data = JSON.parse(text);
    if (!data || typeof data !== "object") throw new Error("Invalid backup file");
    return { ...defaultState(), ...data, version: 1 };
  }

  global.SRTDB = {
    defaultState,
    loadState,
    saveState,
    exportJson,
    importJson,
  };
})(window);
