"""
game_logic.py
Core Love Letter game logic - cards, deck, player state, and round management.
"""

import random
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional


class CardType(IntEnum):
    GUARD = 1
    PRIEST = 2
    BARON = 3
    HANDMAID = 4
    PRINCE = 5
    KING = 6
    COUNTESS = 7
    PRINCESS = 8


CARD_INFO = {
    CardType.GUARD:    {"name": "Guard",    "count": 5, "desc": "Guess a player's hand (not Guard). If correct, they're eliminated."},
    CardType.PRIEST:   {"name": "Priest",   "count": 2, "desc": "Look at another player's hand."},
    CardType.BARON:    {"name": "Baron",    "count": 2, "desc": "Compare hands; lower card is eliminated."},
    CardType.HANDMAID: {"name": "Handmaid", "count": 2, "desc": "Protected from card effects until your next turn."},
    CardType.PRINCE:   {"name": "Prince",   "count": 2, "desc": "Choose any player (including yourself) to discard and redraw."},
    CardType.KING:     {"name": "King",     "count": 1, "desc": "Trade hands with another player."},
    CardType.COUNTESS: {"name": "Countess", "count": 1, "desc": "Must discard if you have King or Prince in hand."},
    CardType.PRINCESS: {"name": "Princess", "count": 1, "desc": "Eliminated if you discard this card."},
}

TOKENS_TO_WIN = {2: 7, 3: 5, 4: 4}


@dataclass
class Card:
    card_type: CardType

    @property
    def name(self) -> str:
        return CARD_INFO[self.card_type]["name"]

    @property
    def value(self) -> int:
        return int(self.card_type)

    @property
    def description(self) -> str:
        return CARD_INFO[self.card_type]["desc"]

    def __repr__(self):
        return f"Card({self.name}={self.value})"


@dataclass
class Player:
    name: str
    is_ai: bool = False
    hand: list = field(default_factory=list)
    discard_pile: list = field(default_factory=list)
    is_eliminated: bool = False
    is_protected: bool = False  # Handmaid protection
    tokens: int = 0

    def draw(self, card: Card):
        self.hand.append(card)

    def has_card(self, card_type: CardType) -> bool:
        return any(c.card_type == card_type for c in self.hand)

    def must_discard_countess(self) -> bool:
        """Countess must be discarded if holding King or Prince."""
        has_countess = self.has_card(CardType.COUNTESS)
        has_royal = self.has_card(CardType.KING) or self.has_card(CardType.PRINCE)
        return has_countess and has_royal

    def eliminate(self):
        self.is_eliminated = True
        self.discard_pile.extend(self.hand)
        self.hand.clear()

    def reset_for_round(self):
        self.hand.clear()
        self.discard_pile.clear()
        self.is_eliminated = False
        self.is_protected = False

    @property
    def hand_value(self) -> int:
        return self.hand[0].value if self.hand else 0


class Deck:
    def __init__(self):
        self.cards: list[Card] = []
        self.burned_card: Optional[Card] = None
        self._build()

    def _build(self):
        self.cards = []
        for card_type, info in CARD_INFO.items():
            for _ in range(info["count"]):
                self.cards.append(Card(card_type))

    def shuffle(self):
        random.shuffle(self.cards)

    def burn_top(self):
        """Remove top card face-down (standard Love Letter rule)."""
        if self.cards:
            self.burned_card = self.cards.pop()

    def draw(self) -> Optional[Card]:
        return self.cards.pop() if self.cards else None

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def remaining(self) -> int:
        return len(self.cards)


class GameAction:
    """Represents a card play action."""
    def __init__(self, card: Card, target: Optional["Player"] = None, guess: Optional[CardType] = None):
        self.card = card
        self.target = target
        self.guess = guess  # For Guard only


class ActionResult:
    """Result of playing a card."""
    def __init__(self, message: str = "", eliminated: Optional[Player] = None,
                 revealed_card: Optional[Card] = None, success: bool = True):
        self.message = message
        self.eliminated = eliminated
        self.revealed_card = revealed_card
        self.success = success


class LoveLetterGame:
    """Main game state manager."""

    def __init__(self, player_names: list[str], ai_indices: list[int] = None):
        if len(player_names) < 2 or len(player_names) > 4:
            raise ValueError("Love Letter requires 2–4 players.")

        self.players: list[Player] = [
            Player(name=name, is_ai=(i in (ai_indices or [])))
            for i, name in enumerate(player_names)
        ]
        self.num_players = len(self.players)
        self.tokens_to_win = TOKENS_TO_WIN[self.num_players]
        self.deck = Deck()
        self.current_player_idx: int = 0
        self.round_num: int = 0
        self.game_over: bool = False
        self.round_over: bool = False
        self.winner: Optional[Player] = None
        self.round_winner: Optional[Player] = None
        self.last_round_winner: Optional[Player] = None
        self.needs_to_draw: bool = False
        self.action_log: list[str] = []

        self.start_round()

    # ── Round management ──────────────────────────────────────────────────────

    def start_round(self):
        self.round_num += 1
        self.round_over = False
        self.round_winner = None
        if getattr(self, "last_round_winner", None) and self.last_round_winner in self.players:
            self.current_player_idx = self.players.index(self.last_round_winner)
        for p in self.players:
            p.reset_for_round()

        self.deck = Deck()
        self.deck.shuffle()
        self.deck.burn_top()

        # Deal one card to each player
        for p in self.players:
            card = self.deck.draw()
            if card:
                p.draw(card)

        self.needs_to_draw = True

        self.action_log = [f"── Round {self.round_num} begins ──"]

    def _advance_turn(self):
        """Move to the next non-eliminated player."""
        for _ in range(self.num_players):
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players
            if not self.players[self.current_player_idx].is_eliminated:
                self.needs_to_draw = True
                return

    def begin_turn(self) -> Card:
        """Draw a card for the current player. Returns the drawn card."""
        player = self.current_player
        drawn = self.deck.draw()
        if drawn:
            player.draw(drawn)
        self.needs_to_draw = False
        return drawn

    # ── Card play ─────────────────────────────────────────────────────────────

    def play_card(self, card_index: int, target: Optional[Player] = None,
                  guess: Optional[CardType] = None) -> ActionResult:
        """
        Play a card from the current player's hand.
        card_index: 0 or 1 (index in hand)
        """
        player = self.current_player

        if card_index < 0 or card_index >= len(player.hand):
            return ActionResult("Invalid card index.", success=False)

        card = player.hand[card_index]

        # Countess forced discard rule
        if player.must_discard_countess() and card.card_type != CardType.COUNTESS:
            return ActionResult("You must discard the Countess when holding King or Prince!", success=False)

        # Remove card from hand
        player.hand.pop(card_index)
        player.discard_pile.append(card)

        # Princess auto-eliminate
        if card.card_type == CardType.PRINCESS:
            player.eliminate()
            msg = f"{player.name} discarded the Princess and is eliminated!"
            self.action_log.append(msg)
            result = ActionResult(msg, eliminated=player)
            self._check_round_end()
            if not self.round_over:
                self._advance_turn()
            return result

        result = self._apply_effect(card, player, target, guess)
        self.action_log.append(result.message)

        # Remove Handmaid protection at start of own turn (applied after effect)
        player.is_protected = False

        self._check_round_end()
        if not self.round_over:
            self._advance_turn()
        return result

    def _apply_effect(self, card: Card, player: Player, target: Optional[Player],
                      guess: Optional[CardType]) -> ActionResult:
        ct = card.card_type

        if ct == CardType.GUARD:
            if target is None or target.is_protected:
                return ActionResult(f"{player.name} played Guard but no valid target.")
            if target.hand and target.hand[0].card_type == guess:
                target.eliminate()
                return ActionResult(
                    f"{player.name} guessed {CARD_INFO[guess]['name']} correctly! {target.name} is eliminated!",
                    eliminated=target
                )
            return ActionResult(f"{player.name} guessed wrong with Guard.")

        elif ct == CardType.PRIEST:
            if target is None or target.is_protected:
                return ActionResult(f"{player.name} played Priest but no valid target.")
            revealed = target.hand[0] if target.hand else None
            return ActionResult(
                f"{player.name} used Priest on {target.name}.",
                revealed_card=revealed
            )

        elif ct == CardType.BARON:
            if target is None or target.is_protected:
                return ActionResult(f"{player.name} played Baron but no valid target.")
            p_val = player.hand[0].value if player.hand else 0
            t_val = target.hand[0].value if target.hand else 0
            if p_val > t_val:
                target.eliminate()
                return ActionResult(
                    f"{player.name} vs {target.name}: {p_val} > {t_val}. {target.name} eliminated!",
                    eliminated=target
                )
            elif t_val > p_val:
                player.eliminate()
                return ActionResult(
                    f"{player.name} vs {target.name}: {p_val} < {t_val}. {player.name} eliminated!",
                    eliminated=player
                )
            else:
                return ActionResult(f"{player.name} vs {target.name}: tie! No elimination.")

        elif ct == CardType.HANDMAID:
            player.is_protected = True
            return ActionResult(f"{player.name} played Handmaid. Protected until next turn.")

        elif ct == CardType.PRINCE:
            chosen = target if target else player
            if chosen.is_protected and chosen != player:
                return ActionResult(f"{player.name} played Prince but target is protected.")
            discarded = chosen.hand.pop(0) if chosen.hand else None
            if discarded:
                chosen.discard_pile.append(discarded)
                if discarded.card_type == CardType.PRINCESS:
                    chosen.eliminate()
                    return ActionResult(
                        f"{player.name} used Prince on {chosen.name}. They discarded Princess and are eliminated!",
                        eliminated=chosen
                    )
            new_card = self.deck.draw()
            if new_card:
                chosen.draw(new_card)
            return ActionResult(f"{player.name} used Prince on {chosen.name}. They discarded and redrew.")

        elif ct == CardType.KING:
            if target is None or target.is_protected:
                return ActionResult(f"{player.name} played King but no valid target.")
            player.hand, target.hand = target.hand, player.hand
            return ActionResult(f"{player.name} traded hands with {target.name} via King.")

        elif ct == CardType.COUNTESS:
            return ActionResult(f"{player.name} discarded the Countess.")

        return ActionResult(f"{player.name} played {card.name}.")

    # ── Round/Game end ────────────────────────────────────────────────────────

    def _check_round_end(self):
        alive = [p for p in self.players if not p.is_eliminated]

        # One player left
        if len(alive) == 1:
            self.round_winner = alive[0]
            self._end_round()
            return

        # Deck empty
        if self.deck.is_empty():
            # Highest hand wins; tie goes to highest discard sum
            max_val = max(p.hand_value for p in alive)
            top = [p for p in alive if p.hand_value == max_val]
            if len(top) == 1:
                self.round_winner = top[0]
            else:
                # Discard sum tiebreak
                top.sort(key=lambda p: sum(c.value for c in p.discard_pile), reverse=True)
                self.round_winner = top[0]
            self._end_round()

    def _end_round(self):
        self.round_over = True
        if self.round_winner:
            self.last_round_winner = self.round_winner
            self.round_winner.tokens += 1
            self.action_log.append(f"🏆 {self.round_winner.name} wins the round!")
            if self.round_winner.tokens >= self.tokens_to_win:
                self.game_over = True
                self.winner = self.round_winner
                self.action_log.append(f"🎉 {self.winner.name} wins the game!")

    # ── AI logic ──────────────────────────────────────────────────────────────

    def get_ai_action(self) -> dict:
        """Simple AI: choose card and target heuristically."""
        player = self.current_player
        hand = player.hand
        valid_targets = self.get_valid_targets(player)

        # Countess forced
        if player.must_discard_countess():
            idx = next(i for i, c in enumerate(hand) if c.card_type == CardType.COUNTESS)
            return {"card_index": idx, "target": None, "guess": None}

        # Prefer higher value card (simple greedy)
        card_index = 0 if hand[0].value >= hand[1].value else 1
        card = hand[card_index]

        target = valid_targets[0] if valid_targets else None
        guess = CardType.GUARD  # dummy default

        # Guard: guess a non-guard card
        if card.card_type == CardType.GUARD and target:
            for ct in [CardType.PRINCESS, CardType.COUNTESS, CardType.KING,
                       CardType.PRINCE, CardType.BARON, CardType.PRIEST]:
                guess = ct
                break

        return {"card_index": card_index, "target": target, "guess": guess}

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def get_valid_targets(self, player: Player) -> list[Player]:
        """Returns players that can be targeted (alive, not protected, not self)."""
        return [p for p in self.players
                if p != player and not p.is_eliminated and not p.is_protected]

    def alive_players(self) -> list[Player]:
        return [p for p in self.players if not p.is_eliminated]

    def needs_target(self, card: Card) -> bool:
        return card.card_type in (CardType.GUARD, CardType.PRIEST, CardType.BARON, CardType.KING)

    def can_target_self(self, card: Card) -> bool:
        return card.card_type == CardType.PRINCE

    def is_card_playable(self, card: Card) -> bool:
        player = self.current_player
        if player.must_discard_countess() and card.card_type != CardType.COUNTESS:
            return False
        return True
