# Figuarts Vault: setup (about 10 minutes)

1. Create a free GitHub account, then a new **public** repository (e.g. `figuarts-vault`).
2. Upload everything in this folder (drag and drop works on github.com), including the hidden `.github` folder.
3. Edit `update_catalog.py` line with `UA =` and put your real email where it says YOUR_EMAIL_HERE.
4. Repo **Settings > Pages**: Source = "Deploy from a branch", Branch = `main`, folder `/ (root)`. Your site goes live at `https://YOURNAME.github.io/figuarts-vault/`.
5. Repo **Actions** tab: enable workflows, open "Update catalog", click **Run workflow**.
6. Wait ~3 minutes, then open `catalog.json` in the repo. It should list far more than 27 figures.
   If the run shows a red X ("Too few figures parsed"), the site layout differs from what the script expects. Paste me the error and I'll fix the parser.
7. After that it updates itself every Monday and Friday.

Before you rely on the scraper, read https://tamashiiweb.com/notice/ (their Terms of Use) and decide you're comfortable.
The script only reads public listing pages, honors robots.txt, identifies itself, and waits 1.5s between requests.

Affiliate IDs: set `amazonTag` near the top of the script block in `index.html`.
