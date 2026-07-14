# Project structure

```
study-routine-tracker/
├── app.py                 # Streamlit entry (Cloud-friendly)
├── desktop_companion.py   # Desktop coach launcher
├── deathstar_watcher.py   # Optional Death Star widget launcher
├── Start Tracker.bat      # One-click Windows start (→ launchers/)
├── README.md · LICENSE
├── requirements.txt
├── requirements-reflex.txt
│
├── tracker/               # Main Streamlit app package
│   ├── ui.py              # UI pages/tabs
│   ├── database.py        # SQLite persistence
│   ├── paths.py           # Project root, assets, data dirs
│   ├── garden*.py         # Study Garden
│   ├── logbook.py · pro.py · showup_grid.py · …
│   └── desktop_companion.py · deathstar_watcher.py
│
├── study_tracker/         # Optional Reflex multipage app
├── assets/                # Favicon, stickers, CSS, games assets
├── games/                 # Break mini-games (HTML)
├── docs/                  # Screenshots + docs
├── tests/                 # Persistence / migration smoke tests
├── scripts/               # PowerShell helpers
├── launchers/             # Windows .bat control scripts
├── mobile/ · android/     # Mobile / APK experiments
└── alembic/ · rxconfig.py # Reflex DB migrations
```

## Data

Local SQLite defaults to `study_routine_tracker.db` in the **project root**
(or `TRACKER_DATA_DIR` / Streamlit Cloud home path). See `tracker/paths.py`.
