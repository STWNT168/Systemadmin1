# OPSLOG — deploying to GitHub Pages

Three files, no build step needed:

- `index.html` — the app itself (includes a date + time picker on every log entry, so you can log activity for today or backdate it)
- `manifest.json` — web app manifest, makes the page installable as a standalone app on desktop/mobile
- `icon.svg` — the app icon referenced by the manifest

## Steps

1. Create a new repository on GitHub (e.g. `opslog`).
2. Add `index.html`, `manifest.json`, and `icon.svg` to the root of the repo.
3. Commit and push:
   ```bash
   git init
   git add index.html manifest.json icon.svg
   git commit -m "Add OPSLOG"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
4. On GitHub: **Settings → Pages → Source** → select the `main` branch, `/ (root)` folder → **Save**.
5. Your app will be live at `https://<your-username>.github.io/<your-repo>/` within a minute or two.

## Notes

- All data is saved through the in-app storage layer, scoped privately to whoever is using the page — nothing to configure.
- The only external dependency is the Google Fonts stylesheet link in `<head>`; everything else (styles, logic) is inline, so there's nothing else to host or bundle.
- To use a custom domain, add a `CNAME` file to the repo root with your domain name, per GitHub's Pages docs.
