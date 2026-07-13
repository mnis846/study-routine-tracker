# Study Routine Tracker

**A gamified, local-first study planner for any competitive exam or academic goal.**

Set daily targets, log hours, grow your Study Garden, and stay consistent with streaks and a GitHub-style heatmap — without accounts or setup friction.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why this project

Most aspirants fail from inconsistency, not lack of resources. This app turns daily study into a visible habit loop: plan → log → grow → show up again tomorrow.

Built for demos, personal use, and pitching a productized exam-prep toolkit.

## Features

| Area | What you get |
| --- | --- |
| **Daily targets** | Plan morning goals, check off or skip, evening reflection |
| **Hours tracking** | Quick logs, daily goal, weekly charts, study streak |
| **Logbook** | Subject + activity journal |
| **Study Garden** | XP stages + long-prep grove map (foundation path → exam sprint) |
| **Show-up heatmap** | GitHub-style consistency grid |
| **Break games** | Short reset mini-games between sessions |
| **Desktop companion** | Optional Windows tray sticker / study coach |
| **Local-first data** | No login — single local profile, SQLite on device |
| **Free / Pro** | Core free; advanced garden + analytics unlock |

## Quick start

```bash
# 1. Clone
git clone https://github.com/mnis846/study-routine-tracker.git
cd study-routine-tracker

# 2. Environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`). No signup required.

### Windows shortcuts

- `Start Tracker.bat` — launch the app  
- `Tracker Control.bat` / `launchers/` — start/stop helpers  
- `python desktop_companion.py` — optional desktop sticker  

## Streamlit Community Cloud

1. Push this repo to GitHub (already done if you use the public remote).
2. Deploy with entry file: **`app.py`**.
3. Optional secrets: copy `.streamlit/secrets.toml.example` into Cloud **Secrets** for Pro unlock codes.

> **Note:** Cloud storage is ephemeral between sleep/redeploy. For lasting history, run locally or export backups from the app.

## Data storage

| Environment | Database location |
| --- | --- |
| Desktop (default) | `study_routine_tracker.db` next to the app |
| Custom path | Set env `TRACKER_DATA_DIR` |
| Streamlit Cloud | `~/.study_routine_tracker/study_routine_tracker.db` |

The sidebar shows the active database path.

## Tech stack

- **Python + Streamlit** — primary UI  
- **SQLite** — local persistence  
- **Pandas + Plotly** — analytics  
- **Optional Reflex app** (`study_tracker/`) — experimental multi-page UI  

```bash
# Optional Reflex UI
pip install -r requirements-reflex.txt
reflex run
```

## Project layout (high level)

```
app.py                 # Main Streamlit app
database.py            # Local SQLite + study data API
garden*.py             # Study Garden XP + map
desktop_companion.py   # Windows sticker companion
study_tracker/         # Optional Reflex multipage app
assets/                # Stickers, games, styles
scripts/ · launchers/  # Desktop helpers
```

## Roadmap ideas

- Spaced-revision reminders  
- Multi-device sync / export polish  
- Optional accounts when multi-user is needed  
- AI weekly review (local or API)  

## License

MIT — built by aspirants, for aspirants. **Show up daily.**

**GitHub:** https://github.com/mnis846/study-routine-tracker
