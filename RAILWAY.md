# Railway deployment

## Why `railway up` can fail with `413 Payload Too Large`

The CLI uploads **one archive** of your project. Cloudflare (in front of Railway’s upload endpoint) rejects bodies above roughly **~100MB**.

This repo’s **`gfx/`** folder is large (especially `kit_templates/`). Even with `.railwayignore`, **`kit_templates` alone is often >100MB**, so **CLI deploy may never succeed** with full assets.

## Recommended: deploy from GitHub

1. Push this repo to GitHub (same branch you want to deploy).
2. In Railway: **New project** → **Deploy from GitHub** → select repo/branch.
3. Railway **clones** the repo on their builders — **no** giant single browser/CLI upload, so the **413** limit does not apply the same way.
4. Set service variables (e.g. `WORKBENCH_ACCESS_TOKEN`).
5. Generate a **public domain** under the service.

## If you must use the CLI

Keep `.railwayignore` strict (`.git/`, optional `gfx/icons/`, etc.). If you still see **413**, use **GitHub deploy** instead — do not spend time fighting the upload cap.

## Environment variables

| Variable | Purpose |
|----------|--------|
| `WORKBENCH_ACCESS_TOKEN` | Protects workbench routes; use a long random secret. |
| `PORT` | Set automatically by Railway — do not override in `Procfile` usage. |

Start command (if not auto-detected from `Procfile`):

```bash
python -m pip install -q "numpy==2.2.6" && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

(The repo `Procfile` already does this so `numpy` is installed even if a cached build used an old `requirements.txt`.)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'numpy'`** — Confirm **`requirements.txt`** on GitHub includes `numpy`, then **Redeploy** (optionally **Clear build cache**). Push `Procfile` + `requirements.txt` together.
