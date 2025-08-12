import math
import random
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame


Color = Tuple[int, int, int]


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FPS = 60

# Physics (pixels and seconds)
GRAVITY_Y = 500.0  # px/s^2 downward
WIND_MIN = -200.0  # px/s^2 (left)
WIND_MAX = 200.0   # px/s^2 (right)

BUILDING_MIN_WIDTH = 60
BUILDING_MAX_WIDTH = 120
BUILDING_MIN_HEIGHT = 120
BUILDING_MAX_HEIGHT = 380

GORILLA_SIZE = 28  # square side
GORILLA_RADIUS = 16
EXPLOSION_RADIUS = 28
BANANA_RADIUS = 4

BG_COLOR: Color = (20, 24, 38)
SKY_COLOR: Color = (36, 42, 66)
HUD_COLOR: Color = (240, 240, 240)
PLAYER_COLORS: Tuple[Color, Color] = ((255, 174, 66), (203, 108, 230))
BUILDING_COLORS: List[Color] = [
    (49, 78, 116),
    (53, 87, 128),
    (60, 97, 137),
    (67, 106, 149),
]


@dataclass
class Player:
    name: str
    color: Color
    gorilla_pos: Tuple[int, int]  # top-left of gorilla sprite

    @property
    def center(self) -> Tuple[int, int]:
        return (self.gorilla_pos[0] + GORILLA_SIZE // 2, self.gorilla_pos[1] + GORILLA_SIZE // 2)


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    alive: bool = True


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gorilla (QBASIC-style) - Pygame")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.big_font = pygame.font.SysFont("consolas", 28, bold=True)
        # Enable text input for robust digit entry (handles various keyboard layouts)
        try:
            pygame.key.start_text_input()
        except Exception:
            pass

        self.terrain_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.terrain_surface = self.terrain_surface.convert()
        # We will use black (0,0,0) as empty and white/colored as solid
        self.terrain_surface.fill((0, 0, 0))

        self.players: List[Player] = []
        self.current_player_index = 0
        self.wind_ax = 0.0
        self.projectile: Optional[Projectile] = None

        # Input state
        self.awaiting_angle = True
        self.awaiting_power = False
        self.input_str = ""
        self.entered_angle_deg: Optional[int] = None
        self.entered_power: Optional[int] = None

        # Round state
        self.round_over = False
        self.winner: Optional[int] = None

        self.new_round()

    def new_round(self) -> None:
        self.players = []
        self.projectile = None
        self.round_over = False
        self.winner = None
        self.current_player_index = 0
        self.awaiting_angle = True
        self.awaiting_power = False
        self.input_str = ""
        self.entered_angle_deg = None
        self.entered_power = None
        self.wind_ax = random.uniform(WIND_MIN, WIND_MAX)

        self._generate_city_and_gorillas()

    def _generate_city_and_gorillas(self) -> None:
        # Reset terrain
        self.terrain_surface.fill((0, 0, 0))

        x = 0
        buildings: List[pygame.Rect] = []
        while x < SCREEN_WIDTH:
            width = random.randint(BUILDING_MIN_WIDTH, BUILDING_MAX_WIDTH)
            height = random.randint(BUILDING_MIN_HEIGHT, BUILDING_MAX_HEIGHT)
            if x + width > SCREEN_WIDTH:
                width = SCREEN_WIDTH - x
            rect = pygame.Rect(x, SCREEN_HEIGHT - height, width, height)
            buildings.append(rect)
            x += width

        # Draw buildings to terrain
        for i, rect in enumerate(buildings):
            color = BUILDING_COLORS[i % len(BUILDING_COLORS)]
            pygame.draw.rect(self.terrain_surface, color, rect)

        # Choose gorilla buildings
        left_index = random.randint(1, max(2, len(buildings) // 3))
        right_index = random.randint(max(len(buildings) * 2 // 3, left_index + 1), len(buildings) - 2)

        left_build = buildings[left_index]
        right_build = buildings[right_index]

        left_gx = left_build.centerx - GORILLA_SIZE // 2
        left_gy = left_build.top - GORILLA_SIZE
        right_gx = right_build.centerx - GORILLA_SIZE // 2
        right_gy = right_build.top - GORILLA_SIZE

        self.players = [
            Player("P1", PLAYER_COLORS[0], (left_gx, left_gy)),
            Player("P2", PLAYER_COLORS[1], (right_gx, right_gy)),
        ]

    # --------------- Input Handling ---------------
    def handle_keydown(self, key: int) -> None:
        # Allow restart at any time
        if key == pygame.K_r:
            self.new_round()
            return

        if self.round_over:
            return

        if key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if self.projectile is not None:
            # Ignore input during projectile flight
            return

        if key == pygame.K_BACKSPACE:
            self.input_str = self.input_str[:-1]
            return

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._confirm_input()
            return

        # Main number row
        if pygame.K_0 <= key <= pygame.K_9:
            digit = key - pygame.K_0
            if len(self.input_str) < 3:
                self.input_str += str(digit)
            return

        # Numpad digits
        if pygame.K_KP_0 <= key <= pygame.K_KP_9:
            digit = key - pygame.K_KP_0
            if len(self.input_str) < 3:
                self.input_str += str(digit)
            return

    def handle_textinput(self, text: str) -> None:
        # Accept numeric text input from various layouts
        if self.round_over or self.projectile is not None:
            return
        if not (self.awaiting_angle or self.awaiting_power):
            return
        for ch in text:
            if ch.isdigit() and len(self.input_str) < 3:
                self.input_str += ch

    def _confirm_input(self) -> None:
        if self.awaiting_angle:
            if self.input_str == "":
                return
            value = int(self.input_str)
            value = max(0, min(180, value))
            self.entered_angle_deg = value
            self.awaiting_angle = False
            self.awaiting_power = True
            self.input_str = ""
            return

        if self.awaiting_power:
            if self.input_str == "":
                return
            value = int(self.input_str)
            value = max(1, min(100, value))
            self.entered_power = value
            self.awaiting_power = False
            self.input_str = ""
            # Fire!
            self._launch_projectile()

    # --------------- Game Logic ---------------
    def _launch_projectile(self) -> None:
        assert self.entered_angle_deg is not None
        assert self.entered_power is not None

        shooter = self.players[self.current_player_index]
        angle_deg = float(self.entered_angle_deg)
        power = float(self.entered_power)

        # Map power [1..100] to initial speed
        speed = 8.0 * power  # px/s

        # Convert angle. For right player, mirror horizontally
        angle_rad = math.radians(angle_deg)
        if self.current_player_index == 1:
            angle_rad = math.pi - angle_rad

        vx = math.cos(angle_rad) * speed
        vy = -math.sin(angle_rad) * speed  # screen y grows downward

        # Spawn projectile just outside the gorilla hit radius along the firing direction
        dir_x = math.cos(angle_rad)
        dir_y = -math.sin(angle_rad)
        dir_len = math.hypot(dir_x, dir_y) or 1.0
        unit_dir_x = dir_x / dir_len
        unit_dir_y = dir_y / dir_len

        offset = GORILLA_RADIUS + BANANA_RADIUS + 3
        start_cx, start_cy = shooter.center
        start_x = start_cx + unit_dir_x * offset
        start_y = start_cy + unit_dir_y * offset
        self.projectile = Projectile(pos=pygame.Vector2(start_x, start_y), vel=pygame.Vector2(vx, vy))

    def _update_projectile(self, dt: float) -> None:
        if self.projectile is None:
            return

        proj = self.projectile
        if not proj.alive:
            return

        # Integrate velocity with gravity and wind
        proj.vel.x += self.wind_ax * dt
        proj.vel.y += GRAVITY_Y * dt
        proj.pos.x += proj.vel.x * dt
        proj.pos.y += proj.vel.y * dt

        # Check bounds
        if (proj.pos.x < -50 or proj.pos.x > SCREEN_WIDTH + 50 or
                proj.pos.y < -50 or proj.pos.y > SCREEN_HEIGHT + 50):
            self._end_shot(hit_pos=None)
            return

        # Collision with gorillas first (direct hit)
        for idx, p in enumerate(self.players):
            if self._circle_hit(proj.pos, BANANA_RADIUS, pygame.Vector2(p.center), GORILLA_RADIUS):
                proj.alive = False
                self.winner = 1 - idx
                self._create_explosion((int(proj.pos.x), int(proj.pos.y)))
                self.round_over = True
                return

        # Collision with terrain
        ix = int(round(proj.pos.x))
        iy = int(round(proj.pos.y))
        if 0 <= ix < SCREEN_WIDTH and 0 <= iy < SCREEN_HEIGHT:
            pixel = self.terrain_surface.get_at((ix, iy))
            if pixel != (0, 0, 0, 255) and pixel != (0, 0, 0):
                # Hit building
                proj.alive = False
                self._create_explosion((ix, iy))
                # Check if blast eliminated a gorilla
                self._check_blast_damage((ix, iy))
                self._end_shot(hit_pos=(ix, iy))

    def _end_shot(self, hit_pos: Optional[Tuple[int, int]]) -> None:
        # If winner already set, leave as round over
        if self.winner is not None:
            self.round_over = True
        else:
            # Switch turn
            self.current_player_index = 1 - self.current_player_index
            self.awaiting_angle = True
            self.awaiting_power = False
            self.input_str = ""
            self.entered_angle_deg = None
            self.entered_power = None
        # Remove projectile
        self.projectile = None

    def _create_explosion(self, pos: Tuple[int, int]) -> None:
        # Erase a circle from terrain by overdrawing black
        pygame.draw.circle(self.terrain_surface, (0, 0, 0), pos, EXPLOSION_RADIUS)

    def _check_blast_damage(self, pos: Tuple[int, int]) -> None:
        blast_center = pygame.Vector2(pos)
        for idx, p in enumerate(self.players):
            if self._circle_hit(blast_center, EXPLOSION_RADIUS, pygame.Vector2(p.center), GORILLA_RADIUS):
                # Other player wins
                self.winner = 1 - idx
                self.round_over = True

    @staticmethod
    def _circle_hit(c1: pygame.Vector2, r1: float, c2: pygame.Vector2, r2: float) -> bool:
        return c1.distance_to(c2) <= (r1 + r2)

    # --------------- Rendering ---------------
    def draw(self) -> None:
        self.screen.fill(SKY_COLOR)
        # Terrain
        self.screen.blit(self.terrain_surface, (0, 0))

        # Gorillas
        for idx, p in enumerate(self.players):
            rect = pygame.Rect(p.gorilla_pos[0], p.gorilla_pos[1], GORILLA_SIZE, GORILLA_SIZE)
            pygame.draw.rect(self.screen, p.color, rect, border_radius=6)
            # Eyes
            eye_y = p.gorilla_pos[1] + 9
            pygame.draw.circle(self.screen, (0, 0, 0), (p.gorilla_pos[0] + 9, eye_y), 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (p.gorilla_pos[0] + GORILLA_SIZE - 9, eye_y), 3)

        # Projectile
        if self.projectile is not None and self.projectile.alive:
            pygame.draw.circle(
                self.screen,
                (255, 235, 59),
                (int(self.projectile.pos.x), int(self.projectile.pos.y)),
                BANANA_RADIUS,
            )

        # HUD
        self._draw_hud()

        pygame.display.flip()

    def _draw_hud(self) -> None:
        top_bg_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 50)
        pygame.draw.rect(self.screen, BG_COLOR, top_bg_rect)

        # Wind arrow and value (right-aligned)
        cy = 25
        display_wind = self.wind_ax / ((WIND_MAX - WIND_MIN) / 20.0)
        display_text = f"Viento: {display_wind:+.1f}"
        text_surf = self.font.render(display_text, True, HUD_COLOR)
        right_margin = SCREEN_WIDTH - 16
        text_x = right_margin - text_surf.get_width()
        self.screen.blit(text_surf, (text_x, cy - text_surf.get_height() // 2))

        # Arrow next to the label, also right-aligned
        arrow_len = 80
        arrow_right = text_x - 8
        arrow_left = arrow_right - arrow_len
        norm = max(-1.0, min(1.0, self.wind_ax / WIND_MAX))
        mid_y = cy
        end_x = int((arrow_left + arrow_right) / 2 + (arrow_len / 2) * norm)
        pygame.draw.line(self.screen, HUD_COLOR, (arrow_left, mid_y), (arrow_right, mid_y), 2)
        pygame.draw.line(self.screen, (255, 120, 120), ((arrow_left + arrow_right) // 2, mid_y), (end_x, mid_y), 4)
        head_dir = 1 if end_x >= (arrow_left + arrow_right) // 2 else -1
        pygame.draw.polygon(self.screen, (255, 120, 120), [
            (end_x, mid_y),
            (end_x - 8 * head_dir, mid_y - 6),
            (end_x - 8 * head_dir, mid_y + 6),
        ])

        # Turn and input prompt
        if self.round_over:
            msg = "Empate. R para reiniciar" if self.winner is None else f"Ganó {self.players[self.winner].name}. R para reiniciar"
            end_surf = self.big_font.render(msg, True, HUD_COLOR)
            self.screen.blit(end_surf, (20, 12))
            return

        shooter = self.players[self.current_player_index]
        turn_text = f"Turno: {shooter.name}"
        turn_surf = self.big_font.render(turn_text, True, shooter.color)
        self.screen.blit(turn_surf, (20, 12))

        if self.projectile is None:
            if self.awaiting_angle:
                prompt = "Ángulo (0-180): " + self.input_str
            elif self.awaiting_power:
                prompt = "Potencia (1-100): " + self.input_str
            else:
                prompt = ""
            if prompt:
                prompt_surf = self.font.render(prompt, True, HUD_COLOR)
                self.screen.blit(prompt_surf, (250, 16))

    # --------------- Main Loop ---------------
    def run(self) -> None:
        running = True
        while running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.TEXTINPUT:
                    self.handle_textinput(event.text)

            # Update
            if self.projectile is not None and self.projectile.alive and not self.round_over:
                self._update_projectile(dt)

            # Draw
            self.draw()

        pygame.quit()
        sys.exit(0)


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()


