# Project structure

```
study-routine-tracker/
├── app.py                 # Streamlit entry (Cloud-friendly)
├── desktop_companion.py   # Desktop coach launcher
├── Start Tracker.bat      # One-click Windows start
├── README.md · LICENSE
├── requirements.txt
│
├── tracker/               # Main app package
│   ├── ui.py              # Streamlit UI
│   ├── database.py        # SQLite persistence
│   ├── paths.py           # Project root / assets / data dirs
│   ├── garden*.py         # Study Garden
│   ├── logbook.py · pro.py · showup_grid.py · …
│   ├── desktop_companion.py
│   └── coach.py
│
├── assets/                # Favicon, stickers, CSS
├── games/                 # Break mini-games (HTML)
├── docs/                  # Screenshots + this file
├── tests/                 # Persistence smoke tests
├── scripts/               # PowerShell helpers
└── launchers/             # Windows .bat control scripts
```

## Data

Local SQLite: `study_routine_tracker.db` in the project root  
(or `TRACKER_DATA_DIR` / Streamlit Cloud home). See `tracker/paths.py`.
