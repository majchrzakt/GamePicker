# What Should We Play Tonight? (Flask + Peewee + Jinja2)

Enter how many players you have and how many minutes are available; the app
suggests games that fit, ranked by class ratings.

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run --debug        # open http://127.0.0.1:5000
```
The SQLite file `games.db` is created and seeded with 12 games on first start.
Delete `games.db` to reset.

## Test
```bash
pip install pytest && pytest -q
```

## Layout
| File | Purpose |
|---|---|
| `models.py` | Peewee models `Game` and `Rating` (one-to-many), `save()` hooks, seed data |
| `app.py` | Routes (GET and POST) and the module-level `app` object |
| `templates/base.html` | Shared layout; other pages `{% extends %}` it |
| `static/style.css` | Minimal styling |

## Deploy to Render
1. Push this folder to a GitHub repository.
2. On [render.com](https://render.com): **New → Web Service**, connect the repo.
3. Settings: Runtime **Python 3**, Build Command `pip install -r requirements.txt`,
   Start Command `gunicorn app:app`, Instance type **Free**.
4. Click **Create Web Service**; when the build finishes open the `onrender.com` URL.

**Heads-up:** Render's filesystem is ephemeral, so `games.db` is wiped on every
restart/redeploy (the app re-seeds itself). Free services also spin down after
idle and take about a minute to wake. Verify current free-tier details on
Render's pricing page before class. Persistent data needs a Render Disk
(paid) or Postgres.
