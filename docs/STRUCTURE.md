# Project structure

```
study-routine-tracker/
├── app.py                 # Streamlit entry (Cloud-friendly)
├── desktop_companion.py   # Desktop coach launcher
├── Start Tracker.bat      # One-click Windows start
├── Install Autostart.bat  # Windows login autostart
├── README.md · LICENSE
├── requirements.txt
│
├── tracker/               # Main app package
│   ├── ui.py              # Streamlit UI (tablet-friendly layouts)
│   ├── styles.py          # Mobile / tablet CSS
│   ├── app_styles.py      # Desktop dashboard CSS
│   ├── database.py        # SQLite persistence
│   ├── paths.py           # Project root / assets / data dirs
│   ├── garden*.py         # Study Garden (+ touch pan map)
│   ├── logbook.py · pro.py · showup_grid.py · …
│   ├── desktop_companion.py
│   └── coach.py
│
├── assets/                # Favicon, stickers, CSS
├── games/                 # Break mini-games (HTML, touch-ready)
├── docs/                  # Screenshots + this file
├── tests/                 # Persistence smoke tests
├── scripts/               # PowerShell helpers
└── launchers/             # Windows .bat control scripts
```

## Data

Local SQLite: `study_routine_tracker.db` in the project root  
(or `TRACKER_DATA_DIR` / Streamlit Cloud home). See `tracker/paths.py`.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Default / laptop-friendly + shared features |
| `tablet-android` | Easy tablet UI (plain language, quick hour buttons, no paywalls) |

Laptop installers (`Start Tracker.bat`, `Install Autostart.bat`, scripts/) stay on all branches.

## Android tablet

Open the Streamlit URL in Chrome. Plain guide: [TABLET_GUIDE.md](TABLET_GUIDE.md).
