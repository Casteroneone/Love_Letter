"""
database.py
SQLite-based storage for game records, round history, and player statistics.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "love_letter.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                played_at   TEXT    NOT NULL,
                num_players INTEGER NOT NULL,
                winner_name TEXT    NOT NULL,
                total_rounds INTEGER NOT NULL,
                duration_sec INTEGER
            );

            CREATE TABLE IF NOT EXISTS game_players (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id     INTEGER NOT NULL REFERENCES games(id),
                player_name TEXT    NOT NULL,
                is_ai       INTEGER NOT NULL DEFAULT 0,
                tokens_won  INTEGER NOT NULL DEFAULT 0,
                final_rank  INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS round_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id     INTEGER NOT NULL REFERENCES games(id),
                round_num   INTEGER NOT NULL,
                winner_name TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS player_stats (
                player_name TEXT PRIMARY KEY,
                games_played INTEGER DEFAULT 0,
                games_won    INTEGER DEFAULT 0,
                rounds_won   INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            );
        """)


def save_game(winner_name: str, num_players: int, total_rounds: int,
              players_data: list[dict], round_winners: list[str],
              duration_sec: int = 0) -> int:
    """
    Persist a completed game.

    players_data: [{"name": str, "is_ai": bool, "tokens": int, "rank": int}]
    round_winners: list of winner names per round
    Returns the new game id.
    """
    played_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO games (played_at, num_players, winner_name, total_rounds, duration_sec) "
            "VALUES (?, ?, ?, ?, ?)",
            (played_at, num_players, winner_name, total_rounds, duration_sec)
        )
        game_id = cur.lastrowid

        for p in players_data:
            conn.execute(
                "INSERT INTO game_players (game_id, player_name, is_ai, tokens_won, final_rank) "
                "VALUES (?, ?, ?, ?, ?)",
                (game_id, p["name"], int(p["is_ai"]), p["tokens"], p["rank"])
            )

        for rnum, rw in enumerate(round_winners, 1):
            conn.execute(
                "INSERT INTO round_log (game_id, round_num, winner_name) VALUES (?, ?, ?)",
                (game_id, rnum, rw)
            )

        # Update aggregated stats
        for p in players_data:
            conn.execute("""
                INSERT INTO player_stats (player_name, games_played, games_won, rounds_won, total_tokens)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(player_name) DO UPDATE SET
                    games_played = games_played + 1,
                    games_won    = games_won    + excluded.games_won,
                    rounds_won   = rounds_won   + excluded.rounds_won,
                    total_tokens = total_tokens + excluded.total_tokens
            """, (
                p["name"],
                1 if p["name"] == winner_name else 0,
                round_winners.count(p["name"]),
                p["tokens"]
            ))

        conn.commit()
    return game_id


def get_recent_games(limit: int = 10) -> list[dict]:
    """Return the most recent completed games."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM games ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_player_stats(player_name: Optional[str] = None) -> list[dict]:
    """Return stats for one player (or all if name is None)."""
    with _get_connection() as conn:
        if player_name:
            rows = conn.execute(
                "SELECT * FROM player_stats WHERE player_name = ?", (player_name,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM player_stats ORDER BY games_won DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def get_leaderboard(limit: int = 10) -> list[dict]:
    """Top players by win rate (min 1 game played)."""
    with _get_connection() as conn:
        rows = conn.execute("""
            SELECT player_name,
                   games_played,
                   games_won,
                   rounds_won,
                   total_tokens,
                   ROUND(CAST(games_won AS REAL) / games_played * 100, 1) AS win_rate
            FROM player_stats
            WHERE games_played > 0
            ORDER BY win_rate DESC, games_won DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_game_detail(game_id: int) -> Optional[dict]:
    """Full detail for a single game including players and rounds."""
    with _get_connection() as conn:
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            return None
        players = conn.execute(
            "SELECT * FROM game_players WHERE game_id = ? ORDER BY final_rank", (game_id,)
        ).fetchall()
        rounds = conn.execute(
            "SELECT * FROM round_log WHERE game_id = ? ORDER BY round_num", (game_id,)
        ).fetchall()
    return {
        "game": dict(game),
        "players": [dict(p) for p in players],
        "rounds": [dict(r) for r in rounds]
    }


def clear_all_data():
    """Wipe all records (for testing/reset)."""
    with _get_connection() as conn:
        conn.executescript("""
            DELETE FROM round_log;
            DELETE FROM game_players;
            DELETE FROM games;
            DELETE FROM player_stats;
        """)
        conn.commit()
