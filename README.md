# Love Letter — Digital Board Game

A faithful Pygame implementation of the classic card game **Love Letter** (2–4 players).

---

## 📦 Project Structure

```
love_letter/
├── main.py                  # Entry point — run this
├── requirements.txt         # pip dependencies
├── environment.yml          # conda environment file
├── data/                    # SQLite database (auto-created)
│   └── love_letter.db
├── assets/                  # Optional: font.ttf for custom font
└── love_letter/             # Main package
    ├── __init__.py
    ├── game_logic.py        # Core rules, cards, players, deck
    ├── gui.py               # All Pygame screens and UI
    ├── database.py          # SQLite storage (game records, stats)
    └── utils.py             # Colors, fonts, drawing helpers, Button
```

---

## 🚀 Setup & Run

### Option A — pip + venv (recommended)

```bash
# 1. Clone / unzip the project
cd love_letter

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the game
python main.py
```

### Option B — Conda

```bash
conda env create -f environment.yml
conda activate love_letter
python main.py
```

---

## 🎮 How to Play

Love Letter is a game of risk, deduction, and luck for 2–4 players.

### Objective
Collect enough **Favor Tokens (♥)** by winning rounds. Tokens needed:
- 2 players → 7 tokens
- 3 players → 5 tokens
- 4 players → 4 tokens

### Round Setup
- All 16 cards are shuffled; one is set aside face-down.
- Each player receives one card.

### On Your Turn
1. **Draw** one card from the deck (you now hold 2 cards).
2. **Play** one card face-up, applying its effect.

### Win Condition
The last player standing, OR the player with the **highest card** when the deck runs out, wins the round and earns a ♥.

---

## 🃏 Card Reference

| Card        | Value | Count | Effect |
|-------------|-------|-------|--------|
| Guard       | 1     | 5     | Guess a player's card (not Guard). Correct → they're eliminated. |
| Priest      | 2     | 2     | Look at another player's hand. |
| Baron       | 3     | 2     | Compare hands; lower card is eliminated (tie = no effect). |
| Handmaid    | 4     | 2     | Protected from all effects until your next turn. |
| Prince      | 5     | 2     | A chosen player discards their hand and redraws. |
| King        | 6     | 1     | Trade hands with another player. |
| Countess    | 7     | 1     | Must discard if you also hold the King or Prince. |
| Princess    | 8     | 1     | If you discard this card, you're eliminated. |

---

## 🖥️ UI Guide

- **Main Menu** → New Game / Leaderboard / Quit
- **Setup** → Set player names, toggle Human/AI per seat (2–4 players)
- **Game Screen**:
  - Click a card once to **select** it (it rises)
  - Click it again to **play** it
  - Overlays appear for target selection and Guard guesses
  - Action log on the right shows what happened
- **Stats Screen** → Leaderboard + recent game history

---

## 💾 Data Storage

Game records are saved automatically to `data/love_letter.db` (SQLite).

Tables:
- `games` — each completed game
- `game_players` — per-player results per game
- `round_log` — round-by-round winners
- `player_stats` — aggregated stats per player name

Use the **Leaderboard** screen to view stats, or **Clear Data** to reset.

---

## 🔧 Requirements

- Python 3.10+
- pygame 2.6.1
- No other external dependencies (SQLite is built into Python)

---

## 📝 Notes

- The game runs fully without modifying any source code on a new PC.
- The `data/` folder and database are created automatically on first run.
- AI opponents use a simple greedy heuristic (plays highest-value card when possible).
