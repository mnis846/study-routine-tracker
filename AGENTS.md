# Agents

This is a **Streamlit + SQLite** study routine tracker (local-first).

## Layout

- `app.py` — Streamlit entrypoint
- `tracker/` — application package (UI, database, garden, desktop coach)
- `tests/` — persistence smoke tests
- `docs/STRUCTURE.md` — full tree

## Commands

```bash
pip install -r requirements.txt
streamlit run app.py
python tests/test_local_db.py
```

Windows: double-click `Start Tracker.bat`.
