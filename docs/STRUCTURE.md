# Project structure

```
study-routine-tracker/
├── app.py                 # Streamlit entry (laptop)
├── desktop_companion.py   # Desktop coach launcher
├── Start Tracker.bat      # One-click Windows Streamlit start
├── Start Tablet App.bat   # Serve offline tablet PWA on LAN
├── Install Autostart.bat  # Windows login autostart (laptop)
├── README.md · LICENSE
├── requirements.txt
│
├── tracker/               # Streamlit app package
│   ├── ui.py              # Streamlit UI
│   ├── styles.py          # Mobile / tablet CSS helpers
│   ├── app_styles.py      # Desktop dashboard CSS
│   ├── database.py        # SQLite persistence
│   ├── paths.py           # Project root / assets / data dirs
│   ├── garden*.py         # Study Garden
│   ├── logbook.py · pro.py · showup_grid.py · …
│   ├── desktop_companion.py
│   └── coach.py
│
├── tablet-app/            # Offline installable tablet PWA
│   ├── index.html
│   ├── sw.js · manifest.webmanifest
│   ├── css/ · js/ · icons/
│   └── README.md
│
├── assets/                # Favicon, stickers, CSS
├── games/                 # Break mini-games (HTML)
├── docs/                  # Screenshots + guides
├── tests/                 # Persistence smoke tests
├── scripts/               # PowerShell helpers
└── launchers/             # Windows .bat control scripts
```

## Data

| App | Storage |
| --- | --- |
| Streamlit (laptop) | `study_routine_tracker.db` (or `TRACKER_DATA_DIR`) |
| Tablet PWA | IndexedDB + localStorage on the device |

See `tracker/paths.py` and `tablet-app/js/db.js`.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Default laptop Streamlit app |
| `tablet-android` | Laptop app + offline tablet PWA |

Laptop installers stay in the repo on both.

## Android tablet

Offline PWA: `tablet-app/` · serve with `Start Tablet App.bat`.  
Guide: [TABLET_GUIDE.md](TABLET_GUIDE.md).
