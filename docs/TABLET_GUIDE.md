# Tablet app guide (offline, local data)

The **tablet app** is a small installable web app in `tablet-app/`.  
It is **not** Streamlit Cloud. Study data is stored **on the device** (browser / installed app storage).

Works for any Android tablet (or phone) with Chrome.

---

## What you get

| Feature | On the tablet |
| --- | --- |
| **Today** | Daily study plan — tick items when done |
| **Hours** | Quick taps (+30 min, +1h, +2h, +3h) |
| **Notes** | Short study log with subject |
| **Heatmap** | Calendar of study days |
| **Garden** | XP + trees grow from consistency |
| **Install** | Chrome → Install app / Add to Home screen |
| **Offline** | After first open/install, works without network |
| **Backup** | Download / restore JSON from More |

The Windows laptop app (Streamlit + `Start Tracker.bat` + autostart) is separate and stays as-is.

---

## First-time setup (one PC + tablet on same Wi‑Fi)

1. On the **Windows PC**, open the project folder.
2. Double-click **`Start Tablet App.bat`**  
   (or run `scripts\serve_tablet_app.ps1`).
3. Note the tablet URL printed, e.g. `http://192.168.x.x:8765/`
4. On the **tablet**, open that URL in **Chrome**.
5. Tap **⋮** → **Install app** or **Add to Home screen**.
6. Open the new home-screen icon. Progress saves on the tablet.

After install, the PC server is only needed again if you want to update the app files.

Windows Firewall may ask to allow Python — allow it on **private** networks.

---

## Daily use

1. Open **Study Tracker** from the home screen.  
2. **Today** — add what to study; tick boxes when finished.  
3. **Hours** — tap how long you studied.  
4. **Notes** — one short line.  
5. **Garden** — optional; grows from hours and finished plan items.

---

## Settings & backup

Open **More** (or the gear icon):

- Display name  
- Daily hour goal  
- **Download backup** — keep a JSON copy somewhere safe  
- **Restore backup** — load a previous JSON file  

---

## Troubleshooting

| Problem | What to try |
| --- | --- |
| Tablet can’t open the URL | Same Wi‑Fi as the PC; check the IP in the server window; allow firewall |
| No “Install app” | Use Chrome; open via `http://…` (not a file); try **Add to Home screen** |
| Data missing after browser clear | Clearing site data wipes local storage — restore from a backup |
| App looks old after an update | Serve the new `tablet-app/` again, open the URL once, then reopen the icon |

---

## For developers

```bash
cd tablet-app
python -m http.server 8765 --bind 0.0.0.0
```

Files: `index.html`, `css/`, `js/`, `sw.js`, `manifest.webmanifest`.  
Storage: IndexedDB + localStorage key `srt_tablet_state_v1`.
