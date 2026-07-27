# OPSLOG — deploying to GitHub Pages

This app is a single self-contained file (`index.html`) — no build step needed.

## Steps

1. Create a new repository on GitHub (e.g. `opslog`).
2. Add `index.html` to the root of the repo (already named correctly for Pages).
3. Commit and push:
   ```bash
   git init
   git add index.html
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
