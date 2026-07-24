# Phone / tablet install guide

**Problem we solve:** students with only an Android phone or tablet need a real install that works. Browser “Install app” prompts are unreliable (Chrome often hides them on CDNs / misconfigured Pages).

**Robust solution:** a real **Android APK** (Capacitor WebView app) with **local on-device storage**.

Laptop Streamlit install is separate and unchanged.

---

## Recommended: install the Android APK

### Direct download

**https://github.com/mnis846/study-routine-tracker/releases/download/android-latest/StudyTracker.apk**

### Release page

**https://github.com/mnis846/study-routine-tracker/releases/tag/android-latest**

### Steps (student)

1. Open the download link in **Chrome** on the phone/tablet.  
2. Tap **Download**.  
3. Open the file (`StudyTracker.apk`).  
4. If Android warns about unknown apps → **Settings** → allow for Chrome/Files → back → **Install**.  
5. Open **Study Tracker**.  

Data (today’s plan, hours, notes, garden) is stored **on that device only**.

No laptop. No Streamlit. No Play Store account required.

---

## What is in the app

| Feature | Works offline |
| --- | --- |
| Today’s plan + checkboxes | Yes |
| Quick hour logging | Yes |
| Notes / log | Yes |
| Heatmap calendar | Yes |
| Garden XP + trees | Yes |
| Backup JSON import/export | Yes |

---

## For the repo owner

### Build / update the APK

GitHub Action: `.github/workflows/build-android-apk.yml`

- Runs on pushes to `tablet-android` (when `tablet-app/` or `mobile/` change)  
- Or **Actions → Build Android APK → Run workflow**  
- Publishes / updates release tag **`android-latest`** with `StudyTracker.apk`

Share the stable download URL above after the first green run.

### Optional web copy (not the primary install)

Workflow `deploy-tablet-app.yml` publishes static files to branch **`gh-pages`**.

If you want a short web URL:

1. Repo **Settings → Pages**  
2. Source: **Deploy from a branch**  
3. Branch: **`gh-pages`** / **/** (root)  

Then:

- App: `https://mnis846.github.io/study-routine-tracker/`  
- Get page: `https://mnis846.github.io/study-routine-tracker/get.html`  

**Important:** until Pages is set to `gh-pages`, the short URL may still show the old README — use the **APK** link instead.

---

## Why not rely on PWA install only?

| Approach | Reality on Android |
| --- | --- |
| jsDelivr / random CDN | Often **no** Install prompt (SW / installability fails) |
| GitHub Pages pointing at README | Not the app at all |
| “Add to Home screen” only | Easy to miss; not always offline-complete |
| **APK (Capacitor)** | Real install icon, offline WebView, local storage — **reliable** |

---

## Laptop users (unchanged)

```text
Start Tracker.bat
Install Autostart.bat
```

Streamlit + SQLite on the PC.

---

## Developers

```text
tablet-app/     # web UI + local IndexedDB storage
mobile/         # Capacitor packaging (www generated in CI)
.github/workflows/build-android-apk.yml
```

Local Capacitor (needs Node + Android SDK):

```bash
cd mobile
npm install
npm run sync-web
npx cap add android   # first time
npx cap sync android
cd android && ./gradlew assembleDebug
```
