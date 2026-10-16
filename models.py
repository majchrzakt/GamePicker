"""Database models for the "What Should We Play Tonight?" picker.

Two tables with a one-to-many relationship: one Game has many Ratings.
"""
import os

from peewee import (
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
)

# DB_PATH lets us point at a different file in tests or on a server.
db = SqliteDatabase(os.environ.get("DB_PATH", "games.db"))


class BaseModel(Model):
    """Every model inherits this so they all share the same database."""

    class Meta:
        database = db


class Game(BaseModel):
    name = CharField(unique=True)
    min_players = IntegerField()
    max_players = IntegerField()
    play_minutes = IntegerField()
    complexity = IntegerField(default=2)  # 1 (easy) to 5 (heavy)

    def save(self, *args, **kwargs):
        """DATABASE HOOK: runs every time a Game is saved.

        Overriding save() lets us clean the data in exactly one place,
        no matter which route (or script) created the Game.
        """
        self.name = " ".join(self.name.split()).title()  # "  catan  " -> "Catan"
        if self.min_players > self.max_players:  # entered backwards? swap.
            self.min_players, self.max_players = self.max_players, self.min_players
        return super().save(*args, **kwargs)

    def average_rating(self):
        """Average stars across this game's ratings (0.0 if unrated)."""
        stars = [r.stars for r in self.ratings]  # 'ratings' comes from backref
        return round(sum(stars) / len(stars), 1) if stars else 0.0


class Rating(BaseModel):
    game = ForeignKeyField(Game, backref="ratings", on_delete="CASCADE")
    voter = CharField()
    stars = IntegerField()  # 1 to 5

    def save(self, *args, **kwargs):
        """DATABASE HOOK: keep stars inside 1..5 and voter tidy."""
        self.stars = max(1, min(5, self.stars))
        self.voter = self.voter.strip().title() or "Anonymous"
        return super().save(*args, **kwargs)


# name, min_players, max_players, minutes, complexity, [(voter, stars), ...]
SEED_GAMES = [
    ("Catan", 3, 4, 90, 2, [("Ana", 4), ("Ben", 3)]),
    ("Ticket To Ride", 2, 5, 60, 2, [("Ana", 5), ("Ben", 4)]),
    ("Carcassonne", 2, 5, 45, 2, [("Ana", 4), ("Ben", 4)]),
    ("Codenames", 4, 8, 20, 1, [("Ana", 5), ("Ben", 5)]),
    ("Azul", 2, 4, 45, 2, [("Ana", 4), ("Ben", 5)]),
    ("Pandemic", 2, 4, 45, 3, [("Ana", 3), ("Ben", 4)]),
    ("Wingspan", 1, 5, 70, 3, [("Ana", 5), ("Ben", 4)]),
    ("Sushi Go", 2, 5, 15, 1, [("Ana", 3), ("Ben", 3)]),
    ("Splendor", 2, 4, 30, 2, [("Ana", 4), ("Ben", 3)]),
    ("Terraforming Mars", 1, 5, 120, 4, [("Ana", 4), ("Ben", 5)]),
    ("Love Letter", 2, 4, 20, 1, [("Ana", 3), ("Ben", 4)]),
    ("Dominion", 2, 4, 30, 3, [("Ana", 4), ("Ben", 4)]),
]


def init_db():
    """Create tables, and seed starter games if the table is empty.

    Seeding on every startup matters on Render: its disk is wiped on each
    deploy/restart, so the app would otherwise come up with no games.
    """
    db.connect(reuse_if_open=True)
    db.create_tables([Game, Rating])
    if Game.select().count() == 0:
        for name, lo, hi, mins, cx, ratings in SEED_GAMES:
            game = Game(
                name=name, min_players=lo, max_players=hi,
                play_minutes=mins, complexity=cx,
            )
            game.save()
            for voter, stars in ratings:
                Rating(game=game, voter=voter, stars=stars).save()
    db.close()
