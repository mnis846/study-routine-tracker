# Migrate PC progress → Android phone

Move your Streamlit (laptop) study history into the Android Study Tracker app.

---

## What gets transferred

| From PC (SQLite) | On phone (JSON) |
| --- | --- |
| Study hours by day | Hours + heatmap |
| Daily targets / plans | Today’s plan history |
| Activity logbook | Notes |
| Garden XP + growth events | Garden XP + feed |
| Display name & daily goal | Settings |

Scheduled tests stay PC-only for now (not used on the phone UI).

---

## Steps

### 1) On your Windows PC — create the backup file

**Easiest:** double-click **`Export for Android.bat`** in the project folder.

Or in a terminal:

```bash
python scripts/export_to_android.py
```

Or in the Streamlit app: sidebar → **Export for Android app**.

You’ll get a file like:

`exports/android_backup_YYYY-MM-DD.json`

### 2) Copy the file to your phone

Any method works:

- Google Drive / OneDrive  
- WhatsApp / Telegram (send to yourself)  
- USB cable / Files app  
- Email attachment  

### 3) On the phone — restore into Study Tracker

1. Open **Study Tracker** (the APK app).  
2. Tap **More** (bottom right).  
3. Tap **Restore backup**.  
4. Pick the `android_backup_….json` file.  
5. Wait for “Backup restored”.  

Your hours, plans, notes, and garden XP should appear.

### 4) Keep using the phone

Log new days on the phone as usual.  
Optional: **Download backup** from More once a week.

---

## Tips

- **Restore replaces** the phone’s current Study Tracker data with the file. Export from the phone first if it already has separate progress you care about.  
- PC data is **not deleted** — export is read-only.  
- If export says 0 hours, confirm you’re exporting the DB you actually use (`study_routine_tracker.db` in the project folder, or `TRACKER_DATA_DIR`).  
- Custom DB path:

```bash
python scripts/export_to_android.py --db "D:\path\to\study_routine_tracker.db"
```

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| “Could not read that file” | Use the JSON from Export for Android, not the `.db` file |
| Phone looks empty after restore | Re-export; check the summary lines (hour days / XP) are non-zero |
| Wrong name / goal | Edit under More → Settings after restore |
| Two devices diverge later | Pick one primary device, or re-export/import when you switch |

---

## APK install (if needed)

https://github.com/mnis846/study-routine-tracker/releases/download/android-latest/StudyTracker.apk
