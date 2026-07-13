# Study Routine Tracker

A gamified, local-first study planner for **any competitive exam or academic goal**.

Local-first study tracker (targets, hours, garden map, stickers, break games) for any exam or academic goal.

## Features

- **Daily Targets** — plan and check off goals morning → evening
- **Hours Logging** — daily goal, streak, weekly charts
- **Logbook** — subject + activity journal
- **Study Garden** — XP stages + long-prep grove map (foundation path → exam sprint)
- **Show-up Heatmap** — GitHub-style consistency grid
- **Break Games** — short reset mini-games
- **Desktop Companion** — tray sticker / desktop watcher (Windows)
- **Auth + multi-user** — per-user data isolation (Streamlit + Reflex)
- **Free / Pro tiers** — core free; advanced analytics & full garden path with Pro

## Tech Stack

- **Streamlit** app (`app.py`) — primary full UI
- **Reflex** app (`study_tracker/`) — modern multi-page UI on the same product surface
- **SQLite** — `study_routine_tracker.db`
- **Plotly / Pandas** — charts

## Run (Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run (Reflex)

```bash
pip install -r requirements-reflex.txt
reflex run
```

## Desktop companion

```bash
python desktop_companion.py
```

Or use `Start Tracker.bat` / `launchers/`.

## Terminology

Exam-specific labels from the source tracker are generalized:

| Source term | This project |
| --- | --- |
| CGPSC / Mains | Exam prep / Study Routine |
| Prelims path | Foundation path |
| Mains sprint | Exam sprint |
| State-specific papers | Generic papers / regional subjects |

Customize subjects and daily goals for your own exam.

## License

MIT — built by aspirants, for aspirants. Show up daily.
