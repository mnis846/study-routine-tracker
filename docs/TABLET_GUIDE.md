# Phone / tablet app guide

Offline installable study app in `tablet-app/`.  
**Made for students who only have an Android phone or tablet** (no laptop).

Study data is stored **on that device** (browser / installed app). Not Streamlit Cloud.

---

## What you get

| Feature | On the device |
| --- | --- |
| **Today** | Daily study plan — tick items when done |
| **Hours** | Quick taps (+30 min, +1h, +2h, +3h) |
| **Notes** | Short study log with subject |
| **Heatmap** | Calendar of study days |
| **Garden** | XP + trees grow from consistency |
| **Install** | Chrome → Install app / Add to Home screen |
| **Offline** | After first open, can work without network |
| **Backup** | Download / restore JSON from **More** |

Windows laptop Streamlit app is optional and separate.

---

## Install with only a phone or tablet

No PC. Open **Chrome** on the phone/tablet and use one of these links:

### Link 1 — works immediately (CDN)

**https://cdn.jsdelivr.net/gh/mnis846/study-routine-tracker@tablet-android/tablet-app/index.html**

### Link 2 — short site URL (after Pages points at `gh-pages`)

**https://mnis846.github.io/study-routine-tracker/**

Then:

1. Wait for the app to load.  
2. Tap **⋮** → **Install app** or **Add to Home screen**.  
3. Open the new icon to study.  
4. Progress saves on **this phone/tablet only**.

Share Link 1 (or Link 2) by WhatsApp/SMS — that’s the whole install for a student with no laptop.

---

## One-time: nicer short URL (repo owner)

GitHub Actions publishes the app to the **`gh-pages`** branch on each update.

1. Open the repo on GitHub (any browser, including phone).  
2. **Settings** → **Pages**  
3. **Build and deployment** → Source: **Deploy from a branch**  
4. Branch: **`gh-pages`** / folder **`/` (root)** → Save  

After a minute, Link 2 above serves the tablet app (not the old README page).

Workflow: `.github/workflows/deploy-tablet-app.yml`

---

## Optional: home Wi‑Fi from a PC

Only if someone has the project on Windows:

1. Double-click **`Start Tablet App.bat`**  
2. Open the printed URL on the phone/tablet (same Wi‑Fi)  
3. Install as above  

Not needed when Link 1 or Link 2 works.

---

## Daily use

1. Open **Study Tracker** from the home screen.  
2. **Today** — plan; tick when finished.  
3. **Hours** — tap study time.  
4. **Notes** — one short line.  
5. **Garden** — grows from hours + finished items.

---

## Settings & backup

**More** (or gear):

- Display name  
- Daily hour goal  
- **Download backup** — save JSON to Files / Drive  
- **Restore backup** — if browser data was cleared  

Clearing Chrome site data wipes local progress — keep occasional backups.

---

## Troubleshooting

| Problem | What to try |
| --- | --- |
| Link won’t open | Use Chrome; check mobile data / Wi‑Fi |
| CDN link is old | Wait a few minutes after a new push, or append `?v=2` once |
| No “Install app” | **⋮ → Add to Home screen** still works |
| Short URL shows README | Owner: set Pages branch to **`gh-pages`** (see above) |
| Data missing | Restore a JSON backup |

---

## Developers

```bash
cd tablet-app
python -m http.server 8765 --bind 0.0.0.0
```

Storage: IndexedDB + localStorage (`srt_tablet_state_v1`).
