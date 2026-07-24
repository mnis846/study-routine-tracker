# Study Routine Tracker

### Build unbreakable habits. Show up daily. Grow your Study Garden.

A simple **Streamlit** study tracker for competitive exams or any study goal.

- Plan daily targets  
- Log study hours  
- Keep a subject logbook  
- Grow a Study Garden with XP  
- Track consistency with a GitHub-style heatmap  

**No account.** Laptop data stays in a local SQLite file. Tablet app data stays on the device.

---

## Which app?

| Device | App | Data |
| --- | --- | --- |
| **Windows laptop** | Streamlit (`Start Tracker.bat`, optional autostart) | Local SQLite on the PC |
| **Android phone / tablet** | Offline PWA (`tablet-app/`) via GitHub Pages link or LAN | Local on that device |

Tablet guide: [docs/TABLET_GUIDE.md](docs/TABLET_GUIDE.md)  
Branch **`tablet-android`** carries the tablet PWA; laptop installers remain in the repo.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-FF4B4B)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<p align="center">
  <img src="docs/screenshots/hero.jpg" alt="Study Routine Tracker" width="900" />
</p>

| Targets | Hours | Logbook |
| --- | --- | --- |
| ![Targets](docs/screenshots/dashboard.png) | ![Hours](docs/screenshots/hours.png) | ![Logbook](docs/screenshots/logbook.png) |

| Garden | Break |
| --- | --- |
| ![Garden](docs/screenshots/garden.png) | ![Break](docs/screenshots/break.png) |

---

## Install & run (recommended)

You need **Python 3.10+** ([download](https://www.python.org/downloads/) — on Windows, tick **Add python.exe to PATH**).

```bash
git clone https://github.com/mnis846/study-routine-tracker.git
cd study-routine-tracker

python -m venv venv
```

**Activate the virtual environment**

| OS | Command |
| --- | --- |
| Windows (Command Prompt) | `venv\Scripts\activate` |
| Windows (PowerShell) | `.\venv\Scripts\Activate.ps1` |
| macOS / Linux | `source venv/bin/activate` |

**Install and start**

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501** — no signup. Progress saves automatically.

### Android phone or tablet (no laptop required)

Students with **only a phone or tablet** — no PC, no Streamlit:

1. Open this in **Chrome**:  
   **https://cdn.jsdelivr.net/gh/mnis846/study-routine-tracker@tablet-android/tablet-app/index.html**  
2. **⋮** → **Install app** / **Add to Home screen**  
3. Study with **Today · Hours · Notes · Garden** — data stays **on that device**

Optional short URL (after Pages uses the `gh-pages` branch):  
https://mnis846.github.io/study-routine-tracker/

Optional LAN from a PC: `Start Tablet App.bat`  
Full guide: [docs/TABLET_GUIDE.md](docs/TABLET_GUIDE.md)

### Windows shortcut

After the one-time laptop install above, double-click **`Start Tracker.bat`**.  
It uses the project `venv` and opens the browser.

| File | What it does |
| --- | --- |
| `Start Tracker.bat` | Start the Streamlit laptop app |
| `Start Tablet App.bat` | Serve the tablet PWA for install / update |
| `Tracker Control.bat` | Start / stop / status / autostart |
| `Install Autostart.bat` | Start the laptop app every time Windows logs in |
| `Remove Autostart.bat` | Turn off login autostart |
| `Stop Sticker.bat` | Stop the optional desktop coach |

### Autostart on Windows login

Want the tracker to open automatically when you start your PC?

1. Finish the install steps above once (`venv` + `pip install`).
2. Double-click **`Install Autostart.bat`**  
   (or open **`Tracker Control.bat`** → **6. Install autostart**).

On every login, Streamlit starts in the background and opens **http://localhost:8501**.

**To turn it off anytime:**

- Double-click **`Remove Autostart.bat`**, or  
- **`Tracker Control.bat`** → **7. Remove autostart**, or  
- **3. Stop everything** to close a running session without removing autostart.

---

## Optional: desktop study coach (Windows)

Floating tray sticker for quick hour logs. Not required for the main app.

```bash
# with venv activated
pip install -r requirements-desktop.txt
python desktop_companion.py
```

---

## Your data

| Where you run | Where data is saved |
| --- | --- |
| Windows laptop (Streamlit) | `study_routine_tracker.db` in this folder |
| Custom folder | Env var `TRACKER_DATA_DIR` |
| Android tablet (PWA) | On-device browser storage (IndexedDB / localStorage) |

Laptop: sidebar → **Download full backup (.db)**.  
Tablet: **More** → **Download backup** (JSON).

---

## Project layout

```
app.py              # Streamlit laptop entry
tablet-app/         # Offline tablet PWA
tracker/            # Streamlit app code
Start Tracker.bat   # Laptop start
Start Tablet App.bat# Serve tablet app on LAN
assets/ games/      # Stickers, CSS, break games
requirements.txt    # Core dependencies
```

More detail: [docs/STRUCTURE.md](docs/STRUCTURE.md)

---

## License

[MIT](LICENSE) — free to use, modify, and share.

**GitHub:** https://github.com/mnis846/study-routine-tracker
