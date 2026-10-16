"""Flask app: routes for the "What Should We Play Tonight?" picker.

Run locally:   flask --app app run --debug
Run on Render: gunicorn app:app   (needs the module-level `app` below)
"""
import os

from flask import Flask, abort, redirect, render_template, request, url_for

from models import Game, Rating, db, init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only")


@app.before_request
def open_db():
    db.connect(reuse_if_open=True)


@app.teardown_request
def close_db(exc):
    if not db.is_closed():
        db.close()


@app.get("/")
def index():
    """GET: list every game with its average rating."""
    games = Game.select().order_by(Game.name)
    return render_template("index.html", games=games)


@app.route("/games/new", methods=["GET", "POST"])
def new_game():
    """GET shows the empty form; POST validates it and saves a Game."""
    error = None
    if request.method == "POST":
        try:
            game = Game(
                name=request.form["name"],
                min_players=int(request.form["min_players"]),
                max_players=int(request.form["max_players"]),
                play_minutes=int(request.form["play_minutes"]),
                complexity=int(request.form["complexity"]),
            )
            if not game.name.strip():
                raise ValueError("Name is required.")
            game.save()  # our save() hook tidies the data
            return redirect(url_for("index"))  # Post/Redirect/Get
        except ValueError:
            error = "Please fill in every field with valid numbers."
        except Exception:  # e.g. duplicate name (unique constraint)
            error = "That game already exists."
    return render_template("game_form.html", error=error)


@app.post("/games/<int:game_id>/rate")
def rate_game(game_id):
    """POST: add a Rating, then redirect so a refresh won't re-submit."""
    game = Game.get_or_none(Game.id == game_id) or abort(404)
    try:
        stars = int(request.form["stars"])
    except (KeyError, ValueError):
        abort(400)
    Rating(game=game, voter=request.form.get("voter", ""), stars=stars).save()
    return redirect(url_for("index"))


@app.get("/pick")
def pick():
    """GET: suggest games that fit the players and time, best rated first."""
    players = request.args.get("players", type=int)
    minutes = request.args.get("minutes", type=int)
    results = None
    if players and minutes:
        # List processing: filter with a comprehension...
        fits = [
            g for g in Game.select()
            if g.min_players <= players <= g.max_players
            and g.play_minutes <= minutes
        ]
        # ...then sort by average rating (best first), name breaks ties.
        results = sorted(fits, key=lambda g: (-g.average_rating(), g.name))
    return render_template(
        "pick.html", results=results, players=players, minutes=minutes
    )


init_db()  # create tables + seed at import time so gunicorn gets them too

if __name__ == "__main__":
    app.run(debug=True)
