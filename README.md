# Ops Log — Kivy Android App

Native Python (Kivy) rebuild of the system admin work order tracker.
Built into an APK automatically by GitHub Actions using Buildozer — no local Android setup needed.

## Files
- `main.py` — the entire app (UI + logic), single file
- `buildozer.spec` — Android build configuration
- `.github/workflows/build-apk.yml` — CI workflow that builds the APK on every push

## Get the APK

1. Create a new GitHub repo.
2. Add these 3 files using **Add file → Create new file**, typing the full path as the file name:
   - `main.py`
   - `buildozer.spec`
   - `.github/workflows/build-apk.yml` (the `/` in the name auto-creates the folders)
3. Commit to `main`.
4. Go to the **Actions** tab — "Build APK" starts automatically (first build takes 15–20 min since it compiles the Android toolchain from scratch; later builds are faster).
5. Once green, open the run → **Artifacts** → download `ops-log-apk`, unzip to get the `.apk`.
6. Copy it to your phone and install (allow "install unknown apps" if prompted).

## Notes
- Data is stored locally in a JSON file in the app's private storage on your phone — nothing leaves the device.
- This is a debug build, fine for personal sideloading, not signed for Play Store.
- Package id: `com.lalit.opslog` — change `package.domain` / `package.name` in `buildozer.spec` if you want a different one.
- If the build fails, check the failed step's log in the Actions tab and send me the error — Buildozer failures are almost always a missing requirement or spec typo.
