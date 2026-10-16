import os
import sys

import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from app import app
from models import Game, Rating, db


@pytest.fixture
def client():
    return app.test_client()


def test_seed_loaded():
    assert Game.select().count() == 12


def test_save_hook_tidies_and_swaps():
    g = Game(name="  my   cool game ", min_players=6, max_players=2, play_minutes=30)
    g.save()
    assert g.name == "My Cool Game"
    assert (g.min_players, g.max_players) == (2, 6)


def test_rating_hook_clamps():
    g = Game.get(Game.name == "Catan")
    r = Rating(game=g, voter=" zed ", stars=99)
    r.save()
    assert (r.stars, r.voter) == (5, "Zed")


def test_index(client):
    assert b"Catan" in client.get("/").data


def test_new_game_post_redirects(client):
    resp = client.post("/games/new", data=dict(
        name="chess", min_players=2, max_players=2, play_minutes=40, complexity=3))
    assert resp.status_code == 302
    assert Game.get(Game.name == "Chess")


def test_new_game_bad_input(client):
    resp = client.post("/games/new", data=dict(
        name="x", min_players="a", max_players=2, play_minutes=5, complexity=1))
    assert b"valid numbers" in resp.data


def test_rate(client):
    g = Game.get(Game.name == "Azul")
    before = g.ratings.count()
    resp = client.post(f"/games/{g.id}/rate", data=dict(voter="Cy", stars=5))
    assert resp.status_code == 302
    assert g.ratings.count() == before + 1


def test_pick_ranked(client):
    html = client.get("/pick?players=4&minutes=30").data.decode()
    assert html.index("Codenames") < html.index("Splendor")
    assert "Terraforming" not in html
