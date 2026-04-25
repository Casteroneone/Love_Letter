"""
utils.py
Shared constants, color palette, font helpers, animation utilities, and misc helpers.
"""

import pygame
import os
import math
import random

# ── Window ─────────────────────────────────────────────────────────────────────
SCREEN_W = 1280
SCREEN_H = 800
FPS = 60
TITLE = "Love Letter"

# ── Palette ───────────────────────────────────────────────────────────────────
# Deep crimson + aged parchment + gold — royal card-game aesthetic
COLOR = {
    "bg":           (18,  10,  10),   # Near-black bg
    "parchment":    (235, 220, 185),  # Card face
    "parchment_dk": (200, 180, 145),  # Card border / shadow
    "crimson":      (165,  20,  30),  # Primary accent
    "crimson_dk":   (110,  10,  18),  # Hover / pressed
    "gold":         (212, 175,  55),  # Highlight / tokens
    "gold_dk":      (160, 130,  30),  # Darker gold
    "ink":          ( 25,  15,  15),  # Text on parchment
    "white":        (245, 240, 230),  # Light text
    "grey":         (120, 110, 100),  # Muted text
    "green":        ( 40, 140,  70),  # Success
    "blue":         ( 50, 120, 200),  # Info / Priest revealed
    "overlay":      ( 10,   5,   5, 180),  # Semi-transparent overlay
    "panel":        ( 30,  18,  18),  # Side panels
    "panel_border": ( 80,  40,  40),  # Panel borders
    "eliminated":   ( 60,  30,  30),  # Eliminated player tint
    "protected":    ( 40,  80, 150),  # Handmaid protection tint
    "selected":     (212, 175,  55),  # Selected card border
    "playable":     (165,  20,  30),  # Playable card glow
}

CARD_VALUE_COLOR = {
    1: (100, 100, 100),
    2: (50,  120, 200),
    3: (180,  80,  20),
    4: (40,  140,  70),
    5: (160,  30, 160),
    6: (200, 140,  20),
    7: (180,  20,  20),
    8: (212, 175,  55),
}

# ── Card dimensions ───────────────────────────────────────────────────────────
CARD_W = 100
CARD_H = 150
CARD_RADIUS = 10
MINI_CARD_W = 70
MINI_CARD_H = 105

# ── Font cache ────────────────────────────────────────────────────────────────
_font_cache: dict[tuple, pygame.font.Font] = {}

def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        try:
            # Try to load a custom font if present
            font_path = os.path.join(os.path.dirname(__file__), "..", "assets", "font.ttf")
            if os.path.exists(font_path):
                _font_cache[key] = pygame.font.Font(font_path, size)
            else:
                _font_cache[key] = pygame.font.SysFont("Georgia" if not bold else "Georgia", size, bold=bold)
        except Exception:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_rounded_rect(surface: pygame.Surface, color: tuple, rect: pygame.Rect,
                      radius: int = 8, border: int = 0, border_color: tuple = None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


def draw_text(surface: pygame.Surface, text: str, x: int, y: int,
              color: tuple = None, size: int = 20, bold: bool = False,
              center: bool = False, anchor: str = "topleft") -> pygame.Rect:
    color = color or COLOR["white"]
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    setattr(rect, anchor, (x, y))
    if center:
        rect.centerx = x
    surface.blit(surf, rect)
    return rect


def draw_text_wrapped(surface: pygame.Surface, text: str, rect: pygame.Rect,
                      color: tuple = None, size: int = 16):
    """Draw text wrapped inside a rect."""
    color = color or COLOR["white"]
    font = get_font(size)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + (" " if current else "") + word
        if font.size(test)[0] <= rect.width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    y = rect.top
    line_h = font.get_linesize()
    for line in lines:
        if y + line_h > rect.bottom:
            break
        surf = font.render(line, True, color)
        surface.blit(surf, (rect.left, y))
        y += line_h


def draw_card_back(surface: pygame.Surface, x: int, y: int,
                   w: int = CARD_W, h: int = CARD_H, alpha: int = 255):
    """Draw a card face-down."""
    rect = pygame.Rect(x, y, w, h)
    # Card base
    draw_rounded_rect(surface, COLOR["crimson_dk"], rect, CARD_RADIUS,
                      border=2, border_color=COLOR["gold"])
    # Pattern
    inner = rect.inflate(-8, -8)
    draw_rounded_rect(surface, COLOR["crimson"], inner, CARD_RADIUS - 2,
                      border=1, border_color=COLOR["gold_dk"])
    # Center ornament
    cx, cy = rect.centerx, rect.centery
    for r in [12, 8, 4]:
        pygame.draw.circle(surface, COLOR["gold_dk"], (cx, cy), r, 1)
    draw_beautiful_token(surface, cx - 8, cy - 8, active=True, size=16)

def draw_heart(surface: pygame.Surface, x: int, y: int, size: int, color: tuple):
    """Draws a filled heart shape."""
    r = max(1, size // 4)
    cx1, cy1 = x - r, y - r
    cx2, cy2 = x + r, y - r
    bx, by = x, y + size // 2

    # Draw the two top lobes
    pygame.draw.circle(surface, color, (cx1, cy1), r)
    pygame.draw.circle(surface, color, (cx2, cy2), r)

    # Draw the bottom triangle
    points = [
        (cx1 - r, cy1 + 1),
        (bx, by),
        (cx2 + r, cy2 + 1)
    ]
    pygame.draw.polygon(surface, color, points)
    
    # Smooth the valley between the lobes slightly
    pygame.draw.polygon(surface, color, [(cx1, cy1), (cx2, cy2), (x, y)])

def draw_beautiful_token(surface: pygame.Surface, x: int, y: int, active: bool = True, size: int = 18):
    """Draw a stylized glowing jewel/token instead of just text."""
    r = size // 2
    if active:
        # Glow
        glow = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (212, 175, 55, 60), (r*2, r*2), r*2)
        pygame.draw.circle(glow, (255, 200, 100, 120), (r*2, r*2), int(r*1.2))
        surface.blit(glow, (x - r*2 + r, y - r*2 + r))
        
        # Gem body
        pygame.draw.circle(surface, COLOR["crimson"], (x + r, y + r), r)
        # Gem highlight
        pygame.draw.circle(surface, (255, 100, 100), (x + r - int(r*0.3), y + r - int(r*0.3)), max(1, int(r*0.3)))
        # Gold rim
        pygame.draw.circle(surface, COLOR["gold"], (x + r, y + r), r, max(1, r//4))
    else:
        # Inactive/empty slot
        pygame.draw.circle(surface, COLOR["panel_border"], (x + r, y + r), r, 2)
        pygame.draw.circle(surface, (20, 10, 10), (x + r, y + r), r - 2)

def draw_ornate_borders(surface: pygame.Surface):
    """Draw medieval corner flourishes."""
    color = COLOR["gold_dk"]
    margin = 20
    length = 60
    thickness = 3
    
    # Top-Left
    pygame.draw.line(surface, color, (margin, margin), (margin + length, margin), thickness)
    pygame.draw.line(surface, color, (margin, margin), (margin, margin + length), thickness)
    pygame.draw.circle(surface, color, (margin + length, margin), 4)
    pygame.draw.circle(surface, color, (margin, margin + length), 4)
    
    # Top-Right
    pygame.draw.line(surface, color, (SCREEN_W - margin, margin), (SCREEN_W - margin - length, margin), thickness)
    pygame.draw.line(surface, color, (SCREEN_W - margin, margin), (SCREEN_W - margin, margin + length), thickness)
    pygame.draw.circle(surface, color, (SCREEN_W - margin - length, margin), 4)
    pygame.draw.circle(surface, color, (SCREEN_W - margin, margin + length), 4)

    # Bottom-Left
    pygame.draw.line(surface, color, (margin, SCREEN_H - margin), (margin + length, SCREEN_H - margin), thickness)
    pygame.draw.line(surface, color, (margin, SCREEN_H - margin), (margin, SCREEN_H - margin - length), thickness)
    pygame.draw.circle(surface, color, (margin + length, SCREEN_H - margin), 4)
    pygame.draw.circle(surface, color, (margin, SCREEN_H - margin - length), 4)

    # Bottom-Right
    pygame.draw.line(surface, color, (SCREEN_W - margin, SCREEN_H - margin), (SCREEN_W - margin - length, SCREEN_H - margin), thickness)
    pygame.draw.line(surface, color, (SCREEN_W - margin, SCREEN_H - margin), (SCREEN_W - margin, SCREEN_H - margin - length), thickness)
    pygame.draw.circle(surface, color, (SCREEN_W - margin - length, SCREEN_H - margin), 4)
    pygame.draw.circle(surface, color, (SCREEN_W - margin, SCREEN_H - margin - length), 4)


def draw_card_face(surface: pygame.Surface, card, x: int, y: int,
                   w: int = CARD_W, h: int = CARD_H,
                   selected: bool = False, playable: bool = True,
                   dim: bool = False):
    """Draw a card face-up."""
    from love_letter.game_logic import CARD_INFO
    rect = pygame.Rect(x, y, w, h)

    bg = COLOR["parchment"] if not dim else COLOR["parchment_dk"]
    border_color = (COLOR["selected"] if selected
                    else COLOR["crimson"] if playable
                    else COLOR["parchment_dk"])
    border_w = 3 if (selected or playable) else 1

    # Drop Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    draw_rounded_rect(surface, (0, 0, 0, 80), shadow_rect, CARD_RADIUS)

    # Base Card
    draw_rounded_rect(surface, bg, rect, CARD_RADIUS,
                      border=border_w, border_color=border_color)
                      
    # Inner Gradient for parchment
    if not dim and w > MINI_CARD_W:
        inner_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Gentle radial inner glow
        for r in range(h // 2, 0, -5):
            alpha = max(0, 30 - int((r / (h//2)) * 30))
            pygame.draw.circle(inner_surf, (255, 245, 230, alpha), (w//2, h//2), r)
        surface.blit(inner_surf, (x, y), special_flags=pygame.BLEND_RGBA_ADD)

    val_color = CARD_VALUE_COLOR.get(card.value, COLOR["ink"])
    scale = w / CARD_W

    # Value top-left
    draw_text(surface, str(card.value), x + int(6 * scale), y + int(6 * scale),
              val_color, size=int(22 * scale), bold=True)

    # Name
    draw_text(surface, card.name, x + w // 2, y + int(40 * scale),
              COLOR["ink"], size=int(14 * scale), bold=True, anchor="midtop")

    # Divider
    pygame.draw.line(surface, COLOR["parchment_dk"],
                     (x + int(8 * scale), y + int(60 * scale)),
                     (x + w - int(8 * scale), y + int(60 * scale)), 1)

    # Description (only on full-size cards)
    if scale >= 0.9:
        desc_rect = pygame.Rect(x + 6, y + 65, w - 12, h - 80)
        draw_text_wrapped(surface, card.description, desc_rect, COLOR["ink"], size=11)

    # Value bottom-right
    draw_text(surface, str(card.value), x + w - int(6 * scale), y + h - int(6 * scale),
              val_color, size=int(22 * scale), bold=True, anchor="bottomright")


# ── Animation helpers ─────────────────────────────────────────────────────────

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3

def pulse(tick: int, speed: float = 0.05) -> float:
    """Returns value oscillating 0→1→0."""
    return (math.sin(tick * speed) + 1) / 2


class FloatingText:
    """Animated text that floats up and fades."""
    def __init__(self, text: str, x: int, y: int, color: tuple, size: int = 22, duration: int = 90):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = list(color)
        self.size = size
        self.duration = duration
        self.age = 0
        self.alive = True

    def update(self):
        self.age += 1
        self.y -= 0.8
        progress = self.age / self.duration
        self.color = list(self.color[:3]) + [int(255 * (1 - progress))]
        if self.age >= self.duration:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        font = get_font(self.size, bold=True)
        surf = font.render(self.text, True, self.color[:3])
        surf.set_alpha(self.color[3] if len(self.color) > 3 else 255)
        rect = surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(surf, rect)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1.5, -0.5)
        self.life = random.uniform(1.0, 3.0)
        self.max_life = self.life
        self.size = random.uniform(1, 3)
        self.color = random.choice([(255, 200, 100), (255, 150, 50), (200, 100, 30)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.016 # Approx 1/60th sec
        # Gentle horizontal drift
        self.vx += random.uniform(-0.05, 0.05)
        self.vx = max(-1.0, min(1.0, self.vx))

    def draw(self, surface):
        if self.life <= 0: return
        alpha = int((self.life / self.max_life) * 150)
        surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(surf, (int(self.x), int(self.y)))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self):
        # Spawn new
        if random.random() < 0.3:
            self.particles.append(Particle(random.uniform(0, SCREEN_W), SCREEN_H + 10))
        
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# Global particle system to persist across screens
GLOBAL_PARTICLES = ParticleSystem()

def draw_beautiful_bg(surface: pygame.Surface, tick: int):
    # Base dark color
    surface.fill((12, 5, 5))
    
    # Large radial gradient at center
    cx, cy = SCREEN_W // 2, SCREEN_H // 2
    r_max = 800
    # Pre-render this once ideally, but simple enough to just draw a few circles
    # Pygame doesn't have built-in gradients, so we fake it with large alpha circles
    gradient_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for r in range(r_max, 100, -150):
        alpha = int(lerp(2, 8, 1 - (r / r_max)))
        pygame.draw.circle(gradient_surf, (80, 10, 15, alpha), (cx, cy), r)
    surface.blit(gradient_surf, (0, 0))
    
    GLOBAL_PARTICLES.update()
    GLOBAL_PARTICLES.draw(surface)
    draw_ornate_borders(surface)

# ── Button ────────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, x: int, y: int, w: int, h: int, text: str,
                 color: tuple = None, hover_color: tuple = None,
                 text_color: tuple = None, font_size: int = 20,
                 radius: int = 8):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color or COLOR["crimson"]
        self.hover_color = hover_color or COLOR["crimson_dk"]
        self.text_color = text_color or COLOR["white"]
        self.font_size = font_size
        self.radius = radius
        self.hovered = False
        self.enabled = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if clicked."""
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface):
        color = self.hover_color if self.hovered else self.color
        if not self.enabled:
            color = COLOR["grey"]
        draw_rounded_rect(surface, color, self.rect, self.radius,
                          border=2, border_color=COLOR["gold_dk"])
        cx, cy = self.rect.center
        draw_text(surface, self.text, cx, cy, self.text_color,
                  size=self.font_size, bold=True, anchor="center")
