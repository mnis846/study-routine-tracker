# Tablet / phone app guide

Offline installable study app (`tablet-app/`).  
**Data stays on the phone or tablet** — not on a cloud study database.

Built for students who may have **only an Android phone or tablet** (no laptop).

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
| **Offline** | After first open, works without network |
| **Backup** | Download / restore JSON from **More** |

The Windows laptop Streamlit app is optional and separate.

---

## Path A — Phone or tablet only (recommended)

No PC. No Streamlit. One link in Chrome.

### 1) Published app link

After GitHub Pages is enabled for this repo (see below), open:

**https://mnis846.github.io/study-routine-tracker/**

(If the repo is forked, replace `mnis846` with the GitHub username.)

### 2) Install on the device

1. Open the link in **Chrome** (Android phone or tablet).  
2. Tap **⋮** → **Install app** or **Add to Home screen**.  
3. Open the new icon.  
4. Study offline anytime. Progress is saved on **that device**.

That’s the full install for a student with no laptop.

### One-time setup for the repo owner (any computer or GitHub mobile/web)

GitHub must serve the static files once:

1. Repo → **Settings** → **Pages**  
2. **Source**: GitHub Actions  
3. Push to branch `tablet-android` or `main` (workflow: `.github/workflows/deploy-tablet-app.yml`)  
   — or run **Actions** → **Deploy tablet app** → **Run workflow**  
4. Wait until the workflow is green, then open the Pages URL above.

This is only static file hosting (HTML/JS/CSS). Study logs never go to GitHub Pages; they stay in the browser on the phone/tablet.

---

## Path B — Optional: install over home Wi‑Fi from a PC

Only if you already have the project on a Windows PC and want a local server:

1. Double-click **`Start Tablet App.bat`**  
2. On the phone/tablet (same Wi‑Fi), open the printed URL in Chrome  
3. Install as above  

Not required when Path A is live.

---

## Daily use

1. Open **Study Tracker** from the home screen.  
2. **Today** — plan; tick when finished.  
3. **Hours** — tap how long you studied.  
4. **Notes** — one short line.  
5. **Garden** — grows from hours + finished plan items.

---

## Settings & backup

**More** (or gear):

- Display name  
- Daily hour goal  
- **Download backup** — keep the JSON in Files / Drive  
- **Restore backup** — if the browser data was cleared  

Tip: download a backup weekly. Clearing Chrome site data wipes local progress.

---

## Troubleshooting

| Problem | What to try |
| --- | --- |
| Pages link 404 | Owner: enable Pages (GitHub Actions) and re-run **Deploy tablet app** |
| No “Install app” | Use Chrome; wait for the page to fully load; try **Add to Home screen** |
| Data missing | Browser data was cleared — restore a JSON backup |
| Two devices, different progress | Storage is per device — export/import backup to copy |

---

## Developers

```bash
cd tablet-app
python -m http.server 8765 --bind 0.0.0.0
```

Storage: IndexedDB + localStorage (`srt_tablet_state_v1`).  
Deploy: `.github/workflows/deploy-tablet-app.yml` → GitHub Pages.
