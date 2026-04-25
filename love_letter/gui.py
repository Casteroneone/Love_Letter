"""
gui.py
All Pygame screen classes: MainMenu, PlayerSetup, GameScreen, ResultScreen, StatsScreen.
"""

import pygame
import time
import os
from typing import Optional, Callable

from love_letter.utils import (
    SCREEN_W, SCREEN_H, FPS, TITLE, COLOR, CARD_W, CARD_H,
    draw_rounded_rect, draw_text, draw_card_back, draw_card_face,
    Button, FloatingText, get_font, pulse, ease_out, lerp, draw_beautiful_bg, draw_beautiful_token, draw_heart
)
from love_letter.game_logic import (
    LoveLetterGame, CardType, CARD_INFO, Player, Card
)
from love_letter import database


# ─────────────────────────────────────────────────────────────────────────────
# Base Screen
# ─────────────────────────────────────────────────────────────────────────────

class Screen:
    def __init__(self, app: "App"):
        self.app = app

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        pass

    def _draw_bg(self, surface: pygame.Surface):
        draw_beautiful_bg(surface, getattr(self, "tick", 0))


# ─────────────────────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────────────────────

class MainMenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        cx = SCREEN_W // 2
        self.btns = [
            Button(cx - 120, 340, 240, 55, "New Game",      font_size=22),
            Button(cx - 120, 410, 240, 55, "Leaderboard",   font_size=22,
                   color=COLOR["panel"], hover_color=COLOR["panel_border"]),
            Button(cx - 120, 480, 240, 55, "Quit",          font_size=22,
                   color=(60, 20, 20), hover_color=(90, 30, 30)),
        ]
        self.tick = 0

    def handle_event(self, event):
        if self.btns[0].handle_event(event):
            self.app.set_screen("setup")
        if self.btns[1].handle_event(event):
            self.app.set_screen("stats")
        if self.btns[2].handle_event(event):
            self.app.running = False

    def update(self):
        self.tick += 1

    def draw(self, surface):
        self._draw_bg(surface)

        # Animated hearts
        for i, (ox, oy) in enumerate([(100, 120), (1180, 200), (80, 650), (1200, 600)]):
            alpha = int(60 + 80 * pulse(self.tick + i * 20))
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            draw_heart(s, 30, 30, 40, (*COLOR["crimson"], alpha))
            surface.blit(s, (ox - 30, oy - 30))

        # Title
        draw_text(surface, "  Love Letter  ", SCREEN_W // 2, 160,
                  COLOR["gold"], size=64, bold=True, anchor="center")
        draw_text(surface, "A game of risk, deduction and luck",
                  SCREEN_W // 2, 240, COLOR["grey"], size=22, anchor="center")

        # Ornament line
        pygame.draw.line(surface, COLOR["gold_dk"],
                         (SCREEN_W // 2 - 200, 275), (SCREEN_W // 2 + 200, 275), 1)

        for btn in self.btns:
            btn.draw(surface)

        draw_text(surface, "2 – 4 Players  |  v1.0", SCREEN_W // 2, SCREEN_H - 30,
                  COLOR["grey"], size=14, anchor="center")


# ─────────────────────────────────────────────────────────────────────────────
# Player Setup
# ─────────────────────────────────────────────────────────────────────────────

class SetupScreen(Screen):
    MAX_PLAYERS = 4

    def __init__(self, app):
        super().__init__(app)
        # Default: 2 players (all human)
        self.num_players = 2
        self.player_names = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.is_ai = [False, False, False, False]
        self.editing_idx: Optional[int] = None
        self.cursor_visible = True
        self.cursor_timer = 0

        cx = SCREEN_W // 2
        self.btn_start = Button(cx - 120, 660, 240, 55, "Start Game", font_size=22)
        self.btn_back  = Button(30, 30, 100, 40, "Back",  font_size=18,
                                color=COLOR["panel"], hover_color=COLOR["panel_border"])
        self.btn_add   = Button(cx + 160, 200, 40, 36, "+", font_size=22)
        self.btn_rem   = Button(cx + 210, 200, 40, 36, "−", font_size=22,
                                color=COLOR["panel"], hover_color=COLOR["panel_border"])

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            self.app.set_screen("menu")
            return
        if self.btn_start.handle_event(event):
            self._start_game()
            return
        if self.btn_add.handle_event(event) and self.num_players < self.MAX_PLAYERS:
            self.num_players += 1
            return
        if self.btn_rem.handle_event(event) and self.num_players > 2:
            self.num_players -= 1
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_rect = False
            for i in range(self.num_players):
                name_rect = self._player_rects(i)
                if name_rect.collidepoint(event.pos):
                    self.editing_idx = i
                    if self.player_names[i].startswith("Player "):
                        self.player_names[i] = ""
                    clicked_rect = True
            if not clicked_rect:
                self.editing_idx = None

        if event.type == pygame.KEYDOWN and self.editing_idx is not None:
            idx = self.editing_idx
            if event.key == pygame.K_BACKSPACE:
                self.player_names[idx] = self.player_names[idx][:-1]
            elif event.key == pygame.K_RETURN:
                self.editing_idx = None
            elif len(self.player_names[idx]) < 16:
                self.player_names[idx] += event.unicode

    def _player_rects(self, i: int):
        top = 260 + i * 80
        name_rect = pygame.Rect(SCREEN_W // 2 - 120, top, 240, 44)
        return name_rect

    def _start_game(self):
        names = self.player_names[:self.num_players]
        ai_idx = [i for i in range(self.num_players) if self.is_ai[i]]
        self.app.start_game(names, ai_idx)

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer % 30 == 0:
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface):
        self._draw_bg(surface)
        cx = SCREEN_W // 2

        draw_text(surface, "Game Setup", cx, 80, COLOR["gold"], size=44, bold=True, anchor="center")
        draw_text(surface, "Players", cx - 60, 200, COLOR["white"], size=24, anchor="midleft")
        draw_text(surface, f"{self.num_players}", cx + 140, 210, COLOR["gold"], size=24, bold=True, anchor="center")

        self.btn_add.draw(surface)
        self.btn_rem.draw(surface)

        for i in range(self.num_players):
            name_rect = self._player_rects(i)

            # Name box
            is_editing = self.editing_idx == i
            border = COLOR["gold"] if is_editing else COLOR["panel_border"]
            draw_rounded_rect(surface, COLOR["panel"], name_rect, 8, border=2, border_color=border)
            name_text = self.player_names[i]
            if is_editing and self.cursor_visible:
                name_text += "|"
            draw_text(surface, name_text, name_rect.x + 10, name_rect.centery,
                      COLOR["white"], size=18, anchor="midleft")

        self.btn_start.draw(surface)
        self.btn_back.draw(surface)


# ─────────────────────────────────────────────────────────────────────────────
# Target / Guess Selection Overlay
# ─────────────────────────────────────────────────────────────────────────────

class SelectionOverlay:
    """Modal overlay for choosing a target player or guessing a card."""

    def __init__(self, title: str, options: list, callback: Callable,
                 show_cancel: bool = True):
        self.title = title
        self.options = options  # list of (label, value)
        self.callback = callback
        self.show_cancel = show_cancel
        self.buttons: list[Button] = []
        self._build_buttons()

    def _build_buttons(self):
        cx = SCREEN_W // 2
        start_y = SCREEN_H // 2 - (len(self.options) * 55) // 2
        self.buttons = []
        for i, (label, _) in enumerate(self.options):
            btn = Button(cx - 150, start_y + i * 58, 300, 48, label, font_size=18)
            self.buttons.append(btn)
        if self.show_cancel:
            cancel_y = start_y + len(self.options) * 58 + 10
            self.cancel_btn = Button(cx - 80, cancel_y, 160, 40, "Cancel",
                                     color=COLOR["panel"], hover_color=COLOR["panel_border"],
                                     font_size=16)
        else:
            self.cancel_btn = None

    def handle_event(self, event) -> bool:
        """Returns True if selection was made."""
        for i, btn in enumerate(self.buttons):
            if btn.handle_event(event):
                self.callback(self.options[i][1])
                return True
        if self.cancel_btn and self.cancel_btn.handle_event(event):
            self.callback(None)
            return True
        return False

    def draw(self, surface: pygame.Surface):
        # Dimmed overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Box
        box_h = len(self.options) * 58 + 120 + (50 if self.cancel_btn else 0)
        box_rect = pygame.Rect(SCREEN_W // 2 - 200, SCREEN_H // 2 - box_h // 2, 400, box_h)
        draw_rounded_rect(surface, COLOR["panel"], box_rect, 14,
                          border=2, border_color=COLOR["gold"])

        draw_text(surface, self.title, SCREEN_W // 2, box_rect.top + 30,
                  COLOR["gold"], size=22, bold=True, anchor="center")

        for btn in self.buttons:
            btn.draw(surface)
        if self.cancel_btn:
            self.cancel_btn.draw(surface)


# ─────────────────────────────────────────────────────────────────────────────
# Main Game Screen
# ─────────────────────────────────────────────────────────────────────────────

class GameScreen(Screen):
    def __init__(self, app, game: LoveLetterGame):
        super().__init__(app)
        self.game = game
        self.tick = 0
        self.floating_texts: list[FloatingText] = []
        self.overlay: Optional[SelectionOverlay] = None
        self.selected_card_idx: Optional[int] = None
        self.pending_card_idx: Optional[int] = None
        self.message = ""
        self.message_timer = 0
        self.revealed_card: Optional[Card] = None
        self.revealed_timer = 0
        self.round_start_timer = 0  # brief pause at round start
        self.start_time = time.time()
        self.round_winners: list[str] = []

        # Buttons
        self.btn_end_round = Button(SCREEN_W - 220, SCREEN_H - 70, 180, 50,
                                    "Next Round", font_size=18)
        self.btn_end_game  = Button(SCREEN_W - 220, SCREEN_H - 70, 180, 50,
                                    "View Results", font_size=18)
        self.btn_menu      = Button(20, SCREEN_H - 60, 130, 44, "Menu", font_size=16,
                                    color=COLOR["panel"], hover_color=COLOR["panel_border"])
        self.btn_ready     = Button(SCREEN_W // 2 - 100, SCREEN_H // 2 + 50, 200, 50, "I'm Ready", font_size=20)
        self.deck_rect     = pygame.Rect(SCREEN_W // 2 - 60, 200, CARD_W, CARD_H)

        self.last_human_idx = None
        self.phase = "PLAY"
        
        if not game.current_player.is_ai:
            self.last_human_idx = game.current_player_idx
            self.phase = "PASS_DEVICE" if self._count_humans() > 1 else "DRAW"

        if not game.round_over:
            self._maybe_ai_turn()

    def _count_humans(self):
        return sum(1 for p in self.game.players if not p.is_ai)

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.overlay:
            current_overlay = self.overlay
            if current_overlay.handle_event(event):
                if self.overlay is current_overlay:
                    self.overlay = None
            return

        if self.btn_menu.handle_event(event):
            self._save_and_exit()
            return

        if self.game.round_over:
            if self.game.game_over:
                if self.btn_end_game.handle_event(event):
                    self._save_and_exit(go_results=True)
            else:
                if self.btn_end_round.handle_event(event):
                    self._next_round()
            return

        if self.phase == "PASS_DEVICE":
            if self.btn_ready.handle_event(event):
                self.phase = "DRAW" if self.game.needs_to_draw else "PLAY"
            return

        if self.phase == "DRAW":
            if event.type == pygame.MOUSEBUTTONDOWN and self.deck_rect.collidepoint(event.pos):
                self.game.begin_turn()
                self.phase = "PLAY"
            return

        # Card click (human turn only)
        if self.phase == "PLAY":
            player = self.game.current_player
            if not player.is_ai and not self.game.round_over:
                for i, card in enumerate(player.hand):
                    rect = self._card_rect(i)
                    if event.type == pygame.MOUSEBUTTONDOWN and rect.collidepoint(event.pos):
                        if self.selected_card_idx == i:
                            self._try_play_card(i)
                        else:
                            self.selected_card_idx = i

    def _try_play_card(self, card_idx: int):
        player = self.game.current_player
        card = player.hand[card_idx]

        if not self.game.is_card_playable(card):
            self._show_message("You must discard the Countess!", COLOR["crimson"])
            return

        # Cards that need a target
        if self.game.needs_target(card):
            targets = self.game.get_valid_targets(player)
            if not targets:
                # No valid targets — play the card with no effect
                self._execute_play(card_idx, None, None)
                return

            if card.card_type == CardType.GUARD:
                # First pick target, then pick guess
                self.pending_card_idx = card_idx
                self._prompt_target(targets, after_target_for_guard=True)
            else:
                self.pending_card_idx = card_idx
                self._prompt_target(targets, after_target_for_guard=False)

        elif self.game.can_target_self(card):
            # Prince: choose any alive player
            targets = [player] + self.game.get_valid_targets(player)
            self.pending_card_idx = card_idx
            opts = [(p.name + (" (You)" if p == player else ""), p) for p in targets]
            self.overlay = SelectionOverlay(
                "Choose a player to discard & redraw", opts,
                lambda t: self._execute_play(self.pending_card_idx, t, None)
            )
        else:
            self._execute_play(card_idx, None, None)

    def _prompt_target(self, targets, after_target_for_guard: bool):
        opts = [(p.name, p) for p in targets]

        def on_target(t):
            if t is None:
                return
            if after_target_for_guard:
                self._prompt_guess(t)
            else:
                self._execute_play(self.pending_card_idx, t, None)

        self.overlay = SelectionOverlay("Choose a target", opts, on_target)

    def _prompt_guess(self, target: Player):
        guessable = [ct for ct in CardType if ct != CardType.GUARD]
        opts = [(f"{CARD_INFO[ct]['name']} ({ct})", ct) for ct in guessable]

        def on_guess(g):
            if g is None:
                return
            self._execute_play(self.pending_card_idx, target, g)

        self.overlay = SelectionOverlay(f"Guess {target.name}'s card", opts, on_guess, show_cancel=False)

    def _execute_play(self, card_idx: int, target, guess):
        result = self.game.play_card(card_idx, target, guess)
        self.selected_card_idx = None
        self.pending_card_idx = None
        self._show_message(result.message, COLOR["gold"] if result.success else COLOR["crimson"])

        if result.revealed_card:
            self.revealed_card = result.revealed_card
            self.revealed_timer = 180

        if result.eliminated:
            self.floating_texts.append(
                FloatingText("💀 Eliminated!", SCREEN_W // 2, SCREEN_H // 2,
                             COLOR["crimson"], size=32)
            )

        if self.game.round_over and self.game.round_winner:
            self.round_winners.append(self.game.round_winner.name)

        # AI goes next if not round/game over
        if not self.game.round_over and not self.game.game_over:
            self._maybe_ai_turn()

    # ── AI turn ───────────────────────────────────────────────────────────────

    def _maybe_ai_turn(self):
        """Trigger AI turns automatically."""
        player = self.game.current_player
        if player.is_ai and not self.game.round_over:
            pygame.time.set_timer(pygame.USEREVENT + 1, 800)  # delay for drama

    def _do_ai_turn(self):
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # cancel timer
        if self.game.round_over or self.game.game_over:
            return
        player = self.game.current_player
        if not player.is_ai:
            return

        # Draw card
        self.game.begin_turn()
        action = self.game.get_ai_action()
        result = self.game.play_card(
            action["card_index"], action["target"], action["guess"]
        )
        self._show_message(result.message, COLOR["gold"])

        if result.eliminated:
            self.floating_texts.append(
                FloatingText("💀 Eliminated!", SCREEN_W // 2, SCREEN_H // 2,
                             COLOR["crimson"], size=32)
            )

        if self.game.round_over and self.game.round_winner:
            self.round_winners.append(self.game.round_winner.name)

        if not self.game.round_over:
            self._maybe_ai_turn()

    # ── Round / Game management ───────────────────────────────────────────────

    def _next_round(self):
        self.game.start_round()
        self.selected_card_idx = None
        self.message = ""
        
        curr_p = self.game.current_player
        if not curr_p.is_ai:
            if self._count_humans() > 1 and self.last_human_idx != self.game.current_player_idx:
                self.phase = "PASS_DEVICE"
                self.last_human_idx = self.game.current_player_idx
            else:
                self.phase = "DRAW"
                self.last_human_idx = self.game.current_player_idx
                
        # if AI starts, trigger AI turn
        if curr_p.is_ai:
            self.game.begin_turn()
            self._maybe_ai_turn()

    def _save_and_exit(self, go_results: bool = False):
        duration = int(time.time() - self.start_time)
        winner = self.game.winner or self.game.round_winner
        if winner:
            players_data = [
                {"name": p.name, "is_ai": p.is_ai, "tokens": p.tokens, "rank": i + 1}
                for i, p in enumerate(sorted(self.game.players, key=lambda x: -x.tokens))
            ]
            try:
                database.save_game(
                    winner_name=winner.name,
                    num_players=self.game.num_players,
                    total_rounds=self.game.round_num,
                    players_data=players_data,
                    round_winners=self.round_winners,
                    duration_sec=duration,
                )
            except Exception as e:
                print(f"DB save error: {e}")

        if go_results:
            self.app.set_screen("results", game=self.game)
        else:
            self.app.set_screen("menu")

    def _show_message(self, msg: str, color: tuple = None):
        self.message = msg
        self.message_timer = 180
        self.floating_texts.append(
            FloatingText(msg[:60], SCREEN_W // 2, SCREEN_H // 2 - 50,
                         color or COLOR["gold"], size=20)
        )

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self):
        self.tick += 1
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.alive]
        if self.message_timer > 0:
            self.message_timer -= 1
        if self.revealed_timer > 0:
            self.revealed_timer -= 1

        if not self.game.round_over and not self.game.game_over:
            curr_p = self.game.current_player
            if not curr_p.is_ai:
                if self.last_human_idx != self.game.current_player_idx and self._count_humans() > 1:
                    self.phase = "PASS_DEVICE"
                    self.last_human_idx = self.game.current_player_idx
                elif self.phase not in ("PASS_DEVICE", "DRAW") and self.game.needs_to_draw:
                    self.phase = "DRAW"

        # Listen for AI timer
        events = pygame.event.get(pygame.USEREVENT + 1)
        for e in events:
            self.game.begin_turn()
            self._do_ai_turn()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        self._draw_bg(surface)
        self._draw_table(surface)
        self._draw_players(surface)
        self._draw_deck_area(surface)
        self._draw_player_hand(surface)
        self._draw_log(surface)
        self._draw_hud(surface)

        if self.revealed_card and self.revealed_timer > 0:
            self._draw_revealed_card(surface)

        for ft in self.floating_texts:
            ft.draw(surface)

        if self.overlay:
            self.overlay.draw(surface)

        if self.game.round_over:
            self._draw_round_result(surface)

        self.btn_menu.draw(surface)

    def _draw_table(self, surface):
        # Green baize table feel
        table = pygame.Rect(160, 60, SCREEN_W - 320, SCREEN_H - 260)
        draw_rounded_rect(surface, (20, 45, 20), table, 30,
                          border=3, border_color=(30, 70, 30))

    def _draw_players(self, surface):
        """Draw opponent info panels."""
        bottom_player = self._get_bottom_player()
        opponents = [p for p in self.game.players if p != bottom_player]
        positions = [(SCREEN_W // 2 - 150, 80), (200, 250), (SCREEN_W - 350, 250)]

        for i, p in enumerate(opponents):
            if i >= len(positions):
                break
            x, y = positions[i]
            self._draw_player_panel(surface, p, x, y)

    def _draw_player_panel(self, surface, player: Player, x: int, y: int):
        w, h = 300, 110
        bg = COLOR["eliminated"] if player.is_eliminated else \
             (30, 60, 120) if player.is_protected else COLOR["panel"]
        rect = pygame.Rect(x, y, w, h)
        draw_rounded_rect(surface, bg, rect, 10, border=2, border_color=COLOR["panel_border"])

        # Name
        draw_text(surface, player.name, x + 10, y + 10, COLOR["white"], size=18, bold=True)

        # Token hearts
        for t in range(self.game.tokens_to_win):
            active = t < player.tokens
            draw_beautiful_token(surface, x + 10 + t * 22, y + 40, active=active, size=18)

        # Status badge
        if player.is_eliminated:
            draw_text(surface, "ELIMINATED", x + 10, y + 70, COLOR["crimson"], size=14, bold=True)
        elif player.is_protected:
            draw_text(surface, "🛡 Protected", x + 10, y + 70, COLOR["blue"], size=14)
        else:
            draw_text(surface, f"Cards: {len(player.hand)}", x + 10, y + 70, COLOR["grey"], size=14)

        # Discard pile
        for j, card in enumerate(player.discard_pile[-3:]):
            draw_card_face(surface, card, x + 160 + j * 45, y + 5,
                           w=MINI_CARD_W, h=MINI_CARD_H - 5, dim=True)

        # Current turn indicator
        if self.game.current_player == player and not self.game.round_over:
            pygame.draw.rect(surface, COLOR["gold"], rect, 3, border_radius=10)

    def _draw_deck_area(self, surface):
        # Deck
        cx = SCREEN_W // 2
        if self.phase == "DRAW":
            pygame.draw.rect(surface, COLOR["gold"], self.deck_rect.inflate(8, 8), border_radius=10)
        draw_card_back(surface, cx - 60, 200)
        draw_text(surface, f"{self.game.deck.remaining()}", cx - 60 + CARD_W // 2, 200 + CARD_H + 8,
                  COLOR["grey"], size=16, anchor="center")
        draw_text(surface, "Deck", cx - 60 + CARD_W // 2, 200 + CARD_H + 26,
                  COLOR["grey"], size=13, anchor="center")

        # Tokens legend
        draw_text(surface, f"Need {self.game.tokens_to_win} to win",
                  cx + 80, 210, COLOR["gold_dk"], size=15, anchor="midleft")
        draw_beautiful_token(surface, cx + 220, 210, active=True, size=14)

        # Round
        draw_text(surface, f"Round {self.game.round_num}",
                  cx + 80, 235, COLOR["grey"], size=14, anchor="midleft")

    def _draw_player_hand(self, surface):
        """Draw the human player's hand at the bottom."""
        human = self._get_bottom_player()
        cy = SCREEN_H - 200

        # Player info strip
        strip = pygame.Rect(0, SCREEN_H - 220, SCREEN_W, 220)
        draw_rounded_rect(surface, COLOR["panel"], strip, 0,
                          border=1, border_color=COLOR["panel_border"])

        draw_text(surface, human.name, 20, SCREEN_H - 210,
                  COLOR["gold"], size=20, bold=True)
        for t in range(self.game.tokens_to_win):
            active = t < human.tokens
            draw_beautiful_token(surface, 20 + t * 22, SCREEN_H - 185, active=active, size=18)

        if human.is_protected:
            draw_text(surface, "🛡 Protected this turn", 20, SCREEN_H - 160,
                      COLOR["blue"], size=14)

        if human.is_eliminated:
            draw_text(surface, "You have been eliminated.", 20, SCREEN_H - 155,
                      COLOR["crimson"], size=16)

        # If not human's turn
        is_human_turn = (self.game.current_player == human and not self.game.round_over
                         and not human.is_eliminated)

        if self.phase == "PASS_DEVICE":
            draw_text(surface, f"Pass device to {human.name}", SCREEN_W // 2, SCREEN_H - 120, COLOR["white"], size=24, anchor="center")
            self.btn_ready.draw(surface)
            return

        # Cards
        mouse_pos = pygame.mouse.get_pos()
        if not hasattr(self, 'card_offsets'):
            self.card_offsets = [0.0] * 10
            
        for i, card in enumerate(human.hand):
            rect = self._card_rect(i)
            x, y = rect.topleft
            selected = (self.selected_card_idx == i)
            playable = is_human_turn and self.game.is_card_playable(card) and self.phase == "PLAY"
            hovered = rect.collidepoint(mouse_pos)
            
            target_offset = 0
            if selected:
                target_offset = 20
            elif hovered and playable:
                target_offset = 10
                
            self.card_offsets[i] = lerp(self.card_offsets[i], target_offset, 0.2)
            
            draw_card_face(surface, card, x, y - int(self.card_offsets[i]),
                           selected=selected, playable=playable and not selected)

        if is_human_turn:
            if self.selected_card_idx is not None:
                draw_text(surface, "Click again to play  |  Click another card to switch",
                          SCREEN_W // 2, SCREEN_H - 20, COLOR["grey"], size=14, anchor="center")
            else:
                draw_text(surface, "Click a card to select it",
                          SCREEN_W // 2, SCREEN_H - 20, COLOR["grey"], size=14, anchor="center")

        # Must-play countess warning
        if is_human_turn and human.must_discard_countess():
            draw_text(surface, "⚠ You must discard the Countess!",
                      SCREEN_W // 2, SCREEN_H - 40, COLOR["crimson"], size=16,
                      bold=True, anchor="center")

        # Discard pile
        for j, card in enumerate(human.discard_pile[-5:]):
            draw_card_face(surface, card, SCREEN_W - 400 + j * 50, SCREEN_H - 165,
                           w=MINI_CARD_W, h=MINI_CARD_H, dim=True, playable=False)

    def _card_rect(self, idx: int) -> pygame.Rect:
        hand_size = len(self._get_bottom_player().hand)
        total_w = hand_size * (CARD_W + 20) - 20
        start_x = SCREEN_W // 2 - total_w // 2
        return pygame.Rect(start_x + idx * (CARD_W + 20), SCREEN_H - 205, CARD_W, CARD_H)

    def _draw_log(self, surface):
        log_rect = pygame.Rect(SCREEN_W - 280, 380, 260, 300)
        draw_rounded_rect(surface, COLOR["panel"], log_rect, 8,
                          border=1, border_color=COLOR["panel_border"])
        draw_text(surface, "Action Log", log_rect.x + 10, log_rect.y + 6,
                  COLOR["gold_dk"], size=14, bold=True)
        y = log_rect.y + 28
        for entry in self.game.action_log[-10:]:
            if y + 16 > log_rect.bottom:
                break
            draw_text(surface, entry[:36], log_rect.x + 6, y, COLOR["grey"], size=12)
            y += 16

    def _draw_hud(self, surface):
        # Add turn indicator at the top
        if not self.game.round_over and not self.game.game_over:
            turn_text = f"Current Turn: {self.game.current_player.name}"
            draw_text(surface, turn_text, SCREEN_W // 2, 30, COLOR["gold"], size=24, bold=True, anchor="center")
            
        if self.phase == "DRAW":
            draw_text(surface, "Click the Deck to draw a card", SCREEN_W // 2, 350, COLOR["gold"], size=18, anchor="center")

        if self.message_timer > 0:
            alpha = min(255, self.message_timer * 3)
            s = pygame.Surface((SCREEN_W, 36), pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            surface.blit(s, (0, SCREEN_H // 2 - 100))
            draw_text(surface, self.message, SCREEN_W // 2, SCREEN_H // 2 - 82,
                      COLOR["white"], size=18, anchor="center")

        if self.game.round_over:
            if self.game.game_over:
                self.btn_end_game.draw(surface)
            else:
                self.btn_end_round.draw(surface)

    def _draw_revealed_card(self, surface):
        if not self.revealed_card:
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        cx = SCREEN_W // 2 - CARD_W // 2
        cy = SCREEN_H // 2 - CARD_H // 2
        draw_card_face(surface, self.revealed_card, cx, cy)
        draw_text(surface, "Priest: Revealed Card", SCREEN_W // 2, cy - 30,
                  COLOR["gold"], size=20, bold=True, anchor="center")
        draw_text(surface, "(Click anywhere to continue)", SCREEN_W // 2, cy + CARD_H + 15,
                  COLOR["grey"], size=14, anchor="center")

    def _draw_round_result(self, surface):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(SCREEN_W // 2 - 240, SCREEN_H // 2 - 140, 480, 280)
        draw_rounded_rect(surface, COLOR["panel"], box, 16,
                          border=3, border_color=COLOR["gold"])

        if self.game.game_over and self.game.winner:
            draw_text(surface, "🎉 Game Over!", SCREEN_W // 2, box.top + 30,
                      COLOR["gold"], size=34, bold=True, anchor="center")
            draw_text(surface, f"{self.game.winner.name} wins the game!",
                      SCREEN_W // 2, box.top + 80, COLOR["white"], size=24, anchor="center")
        elif self.game.round_winner:
            draw_text(surface, f"Round {self.game.round_num} Over",
                      SCREEN_W // 2, box.top + 30, COLOR["gold"], size=30, bold=True, anchor="center")
            draw_text(surface, f"{self.game.round_winner.name} wins the round! +1 Jewel",
                      SCREEN_W // 2, box.top + 80, COLOR["white"], size=22, anchor="center")

        # Player scores
        y = box.top + 120
        for p in sorted(self.game.players, key=lambda x: -x.tokens):
            draw_text(surface, f"{p.name}:",
                      SCREEN_W // 2 - 80, y, COLOR["gold"] if p.tokens > 0 else COLOR["grey"],
                      size=18, anchor="center")
            for t in range(self.game.tokens_to_win):
                active = t < p.tokens
                draw_beautiful_token(surface, SCREEN_W // 2 - 20 + t * 22, y, active=active, size=16)
            y += 28

    def _get_bottom_player(self) -> Player:
        if self.last_human_idx is not None:
            return self.game.players[self.last_human_idx]
        return self.game.players[0]


# Needed for mini cards
MINI_CARD_W = 70
MINI_CARD_H = 105


# ─────────────────────────────────────────────────────────────────────────────
# Results Screen
# ─────────────────────────────────────────────────────────────────────────────

class ResultsScreen(Screen):
    def __init__(self, app, game: LoveLetterGame):
        super().__init__(app)
        self.game = game
        cx = SCREEN_W // 2
        self.btn_play_again = Button(cx - 130, 640, 240, 55, "Play Again", font_size=22)
        self.btn_menu       = Button(cx + 130, 640, 160, 55, "Menu", font_size=20,
                                     color=COLOR["panel"], hover_color=COLOR["panel_border"])

    def handle_event(self, event):
        if self.btn_play_again.handle_event(event):
            self.app.set_screen("setup")
        if self.btn_menu.handle_event(event):
            self.app.set_screen("menu")

    def draw(self, surface):
        self._draw_bg(surface)
        cx = SCREEN_W // 2

        draw_text(surface, "Game Results", cx, 60, COLOR["gold"], size=48, bold=True, anchor="center")

        if self.game.winner:
            draw_text(surface, f"🏆  {self.game.winner.name} wins the game!", cx, 150,
                      COLOR["white"], size=28, anchor="center")

        players = sorted(self.game.players, key=lambda p: -p.tokens)
        y = 220
        for rank, p in enumerate(players, 1):
            col = COLOR["gold"] if rank == 1 else COLOR["white"]
            label = f"{rank}. {p.name}" + (" (AI)" if p.is_ai else "")
            draw_text(surface, label, cx - 200, y, col, size=22)
            for t in range(self.game.tokens_to_win):
                active = t < p.tokens
                draw_beautiful_token(surface, cx + 80 + t * 22, y + 10, active=active, size=18)
            y += 48

        draw_text(surface, f"Game lasted {self.game.round_num} round(s).",
                  cx, y + 20, COLOR["grey"], size=18, anchor="center")

        self.btn_play_again.draw(surface)
        self.btn_menu.draw(surface)


# ─────────────────────────────────────────────────────────────────────────────
# Stats / Leaderboard Screen
# ─────────────────────────────────────────────────────────────────────────────

class StatsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.btn_back = Button(30, 30, 120, 44, " Back", font_size=18,
                               color=COLOR["panel"], hover_color=COLOR["panel_border"])
        self.btn_clear = Button(SCREEN_W - 160, 30, 130, 44, "Clear Data", font_size=16,
                                color=(80, 20, 20), hover_color=(110, 30, 30))
        self.leaderboard = []
        self.recent = []
        self._load()

    def _load(self):
        try:
            self.leaderboard = database.get_leaderboard(10)
            self.recent = database.get_recent_games(8)
        except Exception as e:
            print(f"Stats load error: {e}")

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            self.app.set_screen("menu")
        if self.btn_clear.handle_event(event):
            database.clear_all_data()
            self._load()

    def draw(self, surface):
        self._draw_bg(surface)
        cx = SCREEN_W // 2

        draw_text(surface, "Leaderboard & History", cx, 60, COLOR["gold"],
                  size=42, bold=True, anchor="center")

        # Leaderboard table
        lx = 60
        draw_text(surface, "Leaderboard", lx, 120, COLOR["gold"], size=22, bold=True)
        headers = ["Player", "Games", "Wins", "Win %"]
        for j, h in enumerate(headers):
            draw_text(surface, h, lx + j * 160, 155, COLOR["grey"], size=15, bold=True)

        for i, row in enumerate(self.leaderboard):
            y = 180 + i * 32
            col = COLOR["gold"] if i == 0 else COLOR["white"]
            draw_text(surface, row["player_name"][:18], lx, y, col, size=16)
            draw_text(surface, str(row["games_played"]), lx + 160, y, COLOR["white"], size=16)
            draw_text(surface, str(row["games_won"]), lx + 320, y, COLOR["white"], size=16)
            draw_text(surface, f"{row['win_rate']}%", lx + 480, y, COLOR["green"], size=16)

        # Recent games
        rx = cx + 60
        draw_text(surface, "Recent Games", rx, 120, COLOR["gold"], size=22, bold=True)
        for i, game in enumerate(self.recent):
            y = 155 + i * 38
            draw_text(surface, game["played_at"][:16], rx, y, COLOR["grey"], size=13)
            draw_text(surface, f"{game['num_players']}P  |  {game['total_rounds']} rounds",
                      rx + 140, y, COLOR["grey"], size=13)
            draw_text(surface, f"🏆 {game['winner_name']}", rx, y + 16, COLOR["gold"], size=15)

        self.btn_back.draw(surface)
        self.btn_clear.draw(surface)


# ─────────────────────────────────────────────────────────────────────────────
# App (main controller)
# ─────────────────────────────────────────────────────────────────────────────

class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption(TITLE)
        self.screen_surf = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Load background music if present
        music_path = None
        for ext in ["wav", "mp3", "ogg"]:
            path = os.path.join(os.path.dirname(__file__), "..", "assets", f"music.{ext}")
            if os.path.exists(path):
                music_path = path
                break
        if music_path:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)  # Loop forever
            except Exception as e:
                print(f"Failed to play music: {e}")

        self.current_screen: Screen = MainMenuScreen(self)
        database.init_db()

    def set_screen(self, name: str, **kwargs):
        if name == "menu":
            self.current_screen = MainMenuScreen(self)
        elif name == "setup":
            self.current_screen = SetupScreen(self)
        elif name == "game":
            self.current_screen = GameScreen(self, kwargs["game"])
        elif name == "results":
            self.current_screen = ResultsScreen(self, kwargs["game"])
        elif name == "stats":
            self.current_screen = StatsScreen(self)

    def start_game(self, player_names: list[str], ai_indices: list[int]):
        try:
            game = LoveLetterGame(player_names, ai_indices)
            # Human player draws first (already dealt); if human turn, wait for input
            if game.current_player.is_ai:
                game.begin_turn()
            self.set_screen("game", game=game)
        except Exception as e:
            print(f"Game start error: {e}")

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.current_screen.handle_event(event)

            self.current_screen.update()
            self.current_screen.draw(self.screen_surf)
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
