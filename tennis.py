"""
テニスゲーム - Modern Neon Edition
Python + Pygame

操作方法:
  プレイヤー1 (左): W/S キー
  プレイヤー2 (右): 上/下 矢印キー
  一時停止: スペースキー
  リスタート: Rキー
"""

import pygame
import sys
import random
import math
from typing import List, Tuple

# 初期化
pygame.init()
pygame.mixer.init()

# 画面設定
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NEON TENNIS")

# モダンカラーパレット
class Colors:
    # 背景
    BG_DARK = (10, 10, 20)
    BG_GRADIENT_TOP = (15, 15, 35)
    BG_GRADIENT_BOTTOM = (5, 5, 15)

    # ネオンカラー
    NEON_CYAN = (0, 255, 255)
    NEON_PINK = (255, 0, 128)
    NEON_PURPLE = (180, 0, 255)
    NEON_YELLOW = (255, 255, 0)
    NEON_GREEN = (0, 255, 128)
    NEON_ORANGE = (255, 128, 0)

    # UI
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 120)
    DARK_GRAY = (40, 40, 60)

    # プレイヤーカラー
    PLAYER1 = (0, 200, 255)
    PLAYER1_GLOW = (0, 100, 200)
    PLAYER2 = (255, 50, 150)
    PLAYER2_GLOW = (200, 0, 100)

# フォント
try:
    font_large = pygame.font.Font(None, 86)
    font_medium = pygame.font.Font(None, 52)
    font_small = pygame.font.Font(None, 32)
    font_tiny = pygame.font.Font(None, 24)
except:
    font_large = pygame.font.SysFont('arial', 72)
    font_medium = pygame.font.SysFont('arial', 42)
    font_small = pygame.font.SysFont('arial', 28)
    font_tiny = pygame.font.SysFont('arial', 20)

# ゲーム設定
FPS = 60
WINNING_SCORE = 11

# パドル設定
PADDLE_WIDTH = 12
PADDLE_HEIGHT = 100
PADDLE_SPEED = 9

# ボール設定
BALL_SIZE = 14
BALL_SPEED_INITIAL = 8
BALL_SPEED_MAX = 18


def create_glow_surface(size: int, color: Tuple[int, int, int], intensity: float = 1.0) -> pygame.Surface:
    """グロー効果のサーフェスを作成"""
    surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
    for i in range(size * 2, 0, -2):
        alpha = int((i / (size * 2)) * 60 * intensity)
        pygame.draw.circle(surf, (*color, alpha), (size * 2, size * 2), i)
    return surf


def draw_gradient_rect(surface: pygame.Surface, rect: pygame.Rect,
                       color1: Tuple[int, int, int], color2: Tuple[int, int, int], vertical: bool = True):
    """グラデーション矩形を描画"""
    if vertical:
        for i in range(rect.height):
            ratio = i / rect.height
            color = tuple(int(color1[j] + (color2[j] - color1[j]) * ratio) for j in range(3))
            pygame.draw.line(surface, color, (rect.x, rect.y + i), (rect.x + rect.width, rect.y + i))
    else:
        for i in range(rect.width):
            ratio = i / rect.width
            color = tuple(int(color1[j] + (color2[j] - color1[j]) * ratio) for j in range(3))
            pygame.draw.line(surface, color, (rect.x + i, rect.y), (rect.x + i, rect.y + rect.height))


class ScreenShake:
    """スクリーンシェイク効果"""
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.trauma = 0

    def add_trauma(self, amount: float):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self):
        if self.trauma > 0:
            shake = self.trauma ** 2
            self.offset_x = random.uniform(-10, 10) * shake
            self.offset_y = random.uniform(-10, 10) * shake
            self.trauma = max(0, self.trauma - 0.05)
        else:
            self.offset_x = 0
            self.offset_y = 0

    def get_offset(self) -> Tuple[float, float]:
        return self.offset_x, self.offset_y


class Particle:
    """パーティクルエフェクト"""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int],
                 velocity: Tuple[float, float] = None, size: float = 4, life: int = 40):
        self.x = x
        self.y = y
        self.color = color
        if velocity:
            self.dx, self.dy = velocity
        else:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.dx = math.cos(angle) * speed
            self.dy = math.sin(angle) * speed
        self.size = size
        self.initial_life = life
        self.life = life

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dx *= 0.96
        self.dy *= 0.96
        self.life -= 1

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        if self.life > 0:
            ratio = self.life / self.initial_life
            alpha = int(255 * ratio)
            size = int(self.size * ratio)
            if size > 0:
                glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
                # グロー
                for i in range(size * 2, 0, -1):
                    a = int((i / (size * 2)) * alpha * 0.3)
                    pygame.draw.circle(glow_surf, (*self.color, a), (size * 3, size * 3), i + size)
                # コア
                pygame.draw.circle(glow_surf, (*self.color, alpha), (size * 3, size * 3), size)
                surface.blit(glow_surf, (self.x - size * 3 + offset[0], self.y - size * 3 + offset[1]))


class TrailParticle:
    """ボールの軌跡用パーティクル"""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.life = 20
        self.initial_life = 20

    def update(self):
        self.life -= 1

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        if self.life > 0:
            ratio = self.life / self.initial_life
            alpha = int(150 * ratio)
            size = int(BALL_SIZE * 0.6 * ratio)
            if size > 0:
                glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color, alpha), (size * 2, size * 2), size)
                surface.blit(glow_surf, (self.x - size * 2 + offset[0], self.y - size * 2 + offset[1]))


class Paddle:
    """モダンなパドル"""
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], glow_color: Tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.glow_color = glow_color
        self.speed = PADDLE_SPEED
        self.score = 0
        self.target_y = y
        self.hit_flash = 0

    def move_up(self):
        self.rect.y -= self.speed
        if self.rect.top < 60:
            self.rect.top = 60

    def move_down(self):
        self.rect.y += self.speed
        if self.rect.bottom > SCREEN_HEIGHT - 20:
            self.rect.bottom = SCREEN_HEIGHT - 20

    def flash(self):
        self.hit_flash = 10

    def update(self):
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        ox, oy = offset

        # グロー効果
        glow_surf = pygame.Surface((PADDLE_WIDTH + 40, PADDLE_HEIGHT + 40), pygame.SRCALPHA)
        for i in range(20, 0, -2):
            alpha = int((1 - i / 20) * 40)
            if self.hit_flash > 0:
                alpha = int(alpha * 2)
            rect = pygame.Rect(20 - i, 20 - i, PADDLE_WIDTH + i * 2, PADDLE_HEIGHT + i * 2)
            pygame.draw.rect(glow_surf, (*self.glow_color, alpha), rect, border_radius=6)
        surface.blit(glow_surf, (self.rect.x - 20 + ox, self.rect.y - 20 + oy))

        # パドル本体
        color = Colors.WHITE if self.hit_flash > 0 else self.color
        pygame.draw.rect(surface, color,
                        (self.rect.x + ox, self.rect.y + oy, self.rect.width, self.rect.height),
                        border_radius=4)

        # ハイライト
        highlight_rect = pygame.Rect(self.rect.x + 2 + ox, self.rect.y + 2 + oy,
                                    PADDLE_WIDTH - 4, PADDLE_HEIGHT // 3)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (255, 255, 255, 60),
                        (0, 0, highlight_rect.width, highlight_rect.height), border_radius=2)
        surface.blit(highlight_surf, highlight_rect.topleft)


class Ball:
    """ネオンボール"""
    def __init__(self):
        self.trail_particles: List[TrailParticle] = []
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed = BALL_SPEED_INITIAL
        angle = random.uniform(-math.pi/4, math.pi/4)
        direction = random.choice([-1, 1])
        self.dx = direction * self.speed * math.cos(angle)
        self.dy = self.speed * math.sin(angle)
        self.trail_particles.clear()
        self.pulse = 0
        self.color = Colors.NEON_YELLOW

    def move(self):
        # 軌跡パーティクル追加
        if random.random() < 0.8:
            self.trail_particles.append(TrailParticle(self.x, self.y, self.color))

        self.x += self.dx
        self.y += self.dy
        self.pulse = (self.pulse + 0.2) % (math.pi * 2)

        # 軌跡パーティクル更新
        self.trail_particles = [p for p in self.trail_particles if p.life > 0]
        for p in self.trail_particles:
            p.update()

        # 上下の壁で反射
        hit_wall = False
        if self.y - BALL_SIZE // 2 <= 60:
            self.y = 60 + BALL_SIZE // 2
            self.dy = -self.dy
            hit_wall = True
        elif self.y + BALL_SIZE // 2 >= SCREEN_HEIGHT - 20:
            self.y = SCREEN_HEIGHT - 20 - BALL_SIZE // 2
            self.dy = -self.dy
            hit_wall = True

        return hit_wall

    def check_paddle_collision(self, paddle: Paddle) -> bool:
        ball_rect = pygame.Rect(
            self.x - BALL_SIZE // 2,
            self.y - BALL_SIZE // 2,
            BALL_SIZE,
            BALL_SIZE
        )

        if ball_rect.colliderect(paddle.rect):
            relative_y = (self.y - paddle.rect.centery) / (PADDLE_HEIGHT / 2)
            angle = relative_y * (math.pi / 3)

            self.speed = min(self.speed + 0.6, BALL_SPEED_MAX)

            if self.dx < 0:
                self.dx = self.speed * math.cos(angle)
                self.x = paddle.rect.right + BALL_SIZE // 2
            else:
                self.dx = -self.speed * math.cos(angle)
                self.x = paddle.rect.left - BALL_SIZE // 2

            self.dy = self.speed * math.sin(angle)

            # ボールの色を変更
            self.color = random.choice([Colors.NEON_CYAN, Colors.NEON_PINK,
                                       Colors.NEON_YELLOW, Colors.NEON_GREEN, Colors.NEON_ORANGE])
            return True
        return False

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        ox, oy = offset

        # 軌跡
        for p in self.trail_particles:
            p.draw(surface, offset)

        # グロー
        pulse_size = 1 + math.sin(self.pulse) * 0.2
        glow_size = int(BALL_SIZE * 3 * pulse_size)
        glow_surf = create_glow_surface(glow_size, self.color, 1.5)
        surface.blit(glow_surf, (self.x - glow_size * 2 + ox, self.y - glow_size * 2 + oy))

        # ボール本体
        pygame.draw.circle(surface, self.color, (int(self.x + ox), int(self.y + oy)), BALL_SIZE // 2)
        pygame.draw.circle(surface, Colors.WHITE, (int(self.x + ox), int(self.y + oy)), BALL_SIZE // 2 - 3)

        # ハイライト
        highlight_pos = (int(self.x - 2 + ox), int(self.y - 2 + oy))
        pygame.draw.circle(surface, (255, 255, 255, 200), highlight_pos, 3)


class ScorePopup:
    """スコア獲得時のポップアップ"""
    def __init__(self, x: int, y: int, text: str, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 60
        self.initial_life = 60

    def update(self):
        self.y -= 1.5
        self.life -= 1

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        if self.life > 0:
            ratio = self.life / self.initial_life
            alpha = int(255 * ratio)
            scale = 1 + (1 - ratio) * 0.5

            text_surf = font_medium.render(self.text, True, self.color)
            text_surf.set_alpha(alpha)

            scaled_size = (int(text_surf.get_width() * scale), int(text_surf.get_height() * scale))
            scaled_surf = pygame.transform.scale(text_surf, scaled_size)

            surface.blit(scaled_surf,
                        (self.x - scaled_size[0] // 2 + offset[0],
                         self.y - scaled_size[1] // 2 + offset[1]))


class Game:
    """メインゲームクラス"""
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.screen_shake = ScreenShake()
        self.player1 = Paddle(40, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
                             Colors.PLAYER1, Colors.PLAYER1_GLOW)
        self.player2 = Paddle(SCREEN_WIDTH - 40 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
                             Colors.PLAYER2, Colors.PLAYER2_GLOW)
        self.ball = Ball()
        self.particles: List[Particle] = []
        self.popups: List[ScorePopup] = []
        self.paused = False
        self.game_over = False
        self.winner = None
        self.rally_count = 0
        self.max_rally = 0
        self.state = "menu"  # menu, playing, game_over
        self.menu_pulse = 0

        # 背景グリッド用
        self.grid_offset = 0

    def reset(self):
        self.player1.score = 0
        self.player2.score = 0
        self.player1.rect.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
        self.player2.rect.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
        self.ball.reset()
        self.particles.clear()
        self.popups.clear()
        self.game_over = False
        self.winner = None
        self.rally_count = 0
        self.max_rally = 0

    def spawn_hit_particles(self, x: float, y: float, color: Tuple[int, int, int], count: int = 15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def spawn_score_particles(self, x: float, y: float, color: Tuple[int, int, int]):
        for _ in range(40):
            self.particles.append(Particle(x, y, color, size=6, life=60))

    def spawn_wall_particles(self, x: float, y: float):
        color = Colors.NEON_PURPLE
        for _ in range(8):
            angle = random.uniform(-math.pi/4, math.pi/4)
            if y < SCREEN_HEIGHT // 2:
                angle += math.pi / 2
            else:
                angle -= math.pi / 2
            speed = random.uniform(3, 6)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            self.particles.append(Particle(x, y, color, velocity=velocity, size=3, life=25))

    def draw_background(self):
        # グラデーション背景
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            color = tuple(int(Colors.BG_GRADIENT_TOP[i] +
                            (Colors.BG_GRADIENT_BOTTOM[i] - Colors.BG_GRADIENT_TOP[i]) * ratio)
                         for i in range(3))
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

        # アニメーショングリッド
        self.grid_offset = (self.grid_offset + 0.5) % 40
        grid_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for x in range(0, SCREEN_WIDTH + 40, 40):
            alpha = 15 + int(10 * math.sin((x + self.grid_offset) * 0.05))
            pygame.draw.line(grid_surf, (100, 100, 150, alpha),
                           (x - self.grid_offset, 0), (x - self.grid_offset, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            alpha = 15 + int(10 * math.sin((y + self.grid_offset) * 0.05))
            pygame.draw.line(grid_surf, (100, 100, 150, alpha),
                           (0, y - self.grid_offset), (SCREEN_WIDTH, y - self.grid_offset))
        screen.blit(grid_surf, (0, 0))

    def draw_court(self, offset: Tuple[float, float] = (0, 0)):
        ox, oy = offset

        # コート境界線（ネオン）
        border_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 上下の境界
        for i in range(8, 0, -1):
            alpha = int((1 - i / 8) * 60)
            pygame.draw.line(border_surf, (*Colors.NEON_PURPLE, alpha),
                           (20, 60 - i), (SCREEN_WIDTH - 20, 60 - i), 2)
            pygame.draw.line(border_surf, (*Colors.NEON_PURPLE, alpha),
                           (20, SCREEN_HEIGHT - 20 + i), (SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20 + i), 2)

        pygame.draw.line(border_surf, Colors.NEON_PURPLE, (20, 60), (SCREEN_WIDTH - 20, 60), 2)
        pygame.draw.line(border_surf, Colors.NEON_PURPLE, (20, SCREEN_HEIGHT - 20),
                        (SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20), 2)

        screen.blit(border_surf, (ox, oy))

        # センターライン（点線）
        for y in range(70, SCREEN_HEIGHT - 30, 25):
            line_surf = pygame.Surface((4, 12), pygame.SRCALPHA)
            pygame.draw.rect(line_surf, (*Colors.GRAY, 100), (0, 0, 4, 12), border_radius=2)
            screen.blit(line_surf, (SCREEN_WIDTH // 2 - 2 + ox, y + oy))

    def draw_hud(self, offset: Tuple[float, float] = (0, 0)):
        ox, oy = offset

        # スコアボード背景
        header_surf = pygame.Surface((SCREEN_WIDTH, 55), pygame.SRCALPHA)
        pygame.draw.rect(header_surf, (0, 0, 0, 180), (0, 0, SCREEN_WIDTH, 55))
        screen.blit(header_surf, (ox, oy))

        # プレイヤー1スコア
        score1_text = font_medium.render(str(self.player1.score), True, Colors.PLAYER1)
        glow1 = font_medium.render(str(self.player1.score), True, Colors.PLAYER1_GLOW)
        screen.blit(glow1, (102 + ox, 7 + oy))
        screen.blit(score1_text, (100 + ox, 5 + oy))

        label1 = font_tiny.render("PLAYER 1", True, Colors.GRAY)
        screen.blit(label1, (100 + ox, 35 + oy))

        # プレイヤー2スコア
        score2_text = font_medium.render(str(self.player2.score), True, Colors.PLAYER2)
        glow2 = font_medium.render(str(self.player2.score), True, Colors.PLAYER2_GLOW)
        screen.blit(glow2, (SCREEN_WIDTH - 132 + ox, 7 + oy))
        screen.blit(score2_text, (SCREEN_WIDTH - 130 + ox, 5 + oy))

        label2 = font_tiny.render("PLAYER 2", True, Colors.GRAY)
        screen.blit(label2, (SCREEN_WIDTH - 130 + ox, 35 + oy))

        # 中央: ラリーカウント
        if self.rally_count > 0:
            rally_color = Colors.NEON_YELLOW if self.rally_count >= 5 else Colors.GRAY
            rally_text = font_small.render(f"RALLY {self.rally_count}", True, rally_color)
            screen.blit(rally_text, (SCREEN_WIDTH // 2 - rally_text.get_width() // 2 + ox, 15 + oy))

    def draw_menu(self):
        self.draw_background()

        self.menu_pulse = (self.menu_pulse + 0.05) % (math.pi * 2)
        pulse = 0.8 + math.sin(self.menu_pulse) * 0.2

        # タイトル
        title_text = "NEON TENNIS"
        title_surf = font_large.render(title_text, True, Colors.NEON_CYAN)

        # タイトルグロー
        glow_surf = pygame.Surface((title_surf.get_width() + 40, title_surf.get_height() + 40), pygame.SRCALPHA)
        glow_text = font_large.render(title_text, True, Colors.NEON_CYAN)
        for i in range(10, 0, -1):
            alpha = int((1 - i / 10) * 50 * pulse)
            temp_surf = font_large.render(title_text, True, (*Colors.NEON_CYAN[:3], alpha))
            glow_surf.blit(temp_surf, (20 - i, 20 - i))
            glow_surf.blit(temp_surf, (20 + i, 20 + i))
        glow_surf.blit(title_surf, (20, 20))

        screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_surf.get_width() // 2, 150))

        # サブタイトル
        subtitle = font_small.render("MODERN EDITION", True, Colors.NEON_PINK)
        screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 240))

        # スタート指示
        alpha = int(128 + 127 * math.sin(self.menu_pulse * 2))
        start_text = font_medium.render("PRESS SPACE TO START", True, Colors.WHITE)
        start_text.set_alpha(alpha)
        screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 350))

        # 操作説明
        controls = [
            ("PLAYER 1", "W / S", Colors.PLAYER1),
            ("PLAYER 2", "↑ / ↓", Colors.PLAYER2),
        ]

        y_offset = 450
        for label, keys, color in controls:
            label_surf = font_tiny.render(label, True, color)
            keys_surf = font_small.render(keys, True, Colors.WHITE)
            total_width = label_surf.get_width() + 20 + keys_surf.get_width()
            x_start = SCREEN_WIDTH // 2 - total_width // 2
            screen.blit(label_surf, (x_start, y_offset + 5))
            screen.blit(keys_surf, (x_start + label_surf.get_width() + 20, y_offset))
            y_offset += 40

        # フッター
        footer = font_tiny.render("First to 11 wins  |  SPACE: Pause  |  R: Restart", True, Colors.GRAY)
        screen.blit(footer, (SCREEN_WIDTH // 2 - footer.get_width() // 2, SCREEN_HEIGHT - 40))

    def draw_pause_overlay(self, offset: Tuple[float, float] = (0, 0)):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        self.menu_pulse = (self.menu_pulse + 0.05) % (math.pi * 2)

        # PAUSED テキスト
        pause_text = font_large.render("PAUSED", True, Colors.NEON_CYAN)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

        # 再開指示
        alpha = int(128 + 127 * math.sin(self.menu_pulse * 2))
        resume_text = font_small.render("Press SPACE to resume", True, Colors.WHITE)
        resume_text.set_alpha(alpha)
        screen.blit(resume_text, (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def draw_game_over(self, offset: Tuple[float, float] = (0, 0)):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        self.menu_pulse = (self.menu_pulse + 0.05) % (math.pi * 2)

        winner_color = Colors.PLAYER1 if self.winner == 1 else Colors.PLAYER2

        # WINNER テキスト
        winner_text = font_large.render(f"PLAYER {self.winner} WINS!", True, winner_color)
        screen.blit(winner_text, (SCREEN_WIDTH // 2 - winner_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

        # 最終スコア
        score_text = font_medium.render(f"{self.player1.score}  -  {self.player2.score}", True, Colors.WHITE)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        # 最大ラリー
        if self.max_rally > 0:
            rally_text = font_small.render(f"Max Rally: {self.max_rally}", True, Colors.NEON_YELLOW)
            screen.blit(rally_text, (SCREEN_WIDTH // 2 - rally_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))

        # リスタート指示
        alpha = int(128 + 127 * math.sin(self.menu_pulse * 2))
        restart_text = font_small.render("Press R to restart", True, Colors.WHITE)
        restart_text.set_alpha(alpha)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.player1.move_up()
        if keys[pygame.K_s]:
            self.player1.move_down()
        if keys[pygame.K_UP]:
            self.player2.move_up()
        if keys[pygame.K_DOWN]:
            self.player2.move_down()

    def update(self):
        if self.state == "menu":
            return

        if self.paused or self.game_over:
            return

        self.screen_shake.update()
        self.player1.update()
        self.player2.update()

        # ボール移動
        hit_wall = self.ball.move()
        if hit_wall:
            self.spawn_wall_particles(self.ball.x, self.ball.y)
            self.screen_shake.add_trauma(0.1)

        # パドル衝突
        if self.ball.check_paddle_collision(self.player1):
            self.rally_count += 1
            self.max_rally = max(self.max_rally, self.rally_count)
            self.player1.flash()
            self.spawn_hit_particles(self.ball.x, self.ball.y, Colors.PLAYER1)
            self.screen_shake.add_trauma(0.2)

        if self.ball.check_paddle_collision(self.player2):
            self.rally_count += 1
            self.max_rally = max(self.max_rally, self.rally_count)
            self.player2.flash()
            self.spawn_hit_particles(self.ball.x, self.ball.y, Colors.PLAYER2)
            self.screen_shake.add_trauma(0.2)

        # 得点判定
        if self.ball.x < 0:
            self.player2.score += 1
            self.spawn_score_particles(100, SCREEN_HEIGHT // 2, Colors.PLAYER2)
            self.popups.append(ScorePopup(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, "+1", Colors.PLAYER2))
            self.screen_shake.add_trauma(0.4)
            self.rally_count = 0
            self.ball.reset()
        elif self.ball.x > SCREEN_WIDTH:
            self.player1.score += 1
            self.spawn_score_particles(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2, Colors.PLAYER1)
            self.popups.append(ScorePopup(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, "+1", Colors.PLAYER1))
            self.screen_shake.add_trauma(0.4)
            self.rally_count = 0
            self.ball.reset()

        # 勝利判定
        if self.player1.score >= WINNING_SCORE:
            self.game_over = True
            self.winner = 1
        elif self.player2.score >= WINNING_SCORE:
            self.game_over = True
            self.winner = 2

        # パーティクル更新
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # ポップアップ更新
        self.popups = [p for p in self.popups if p.life > 0]
        for p in self.popups:
            p.update()

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
            return

        offset = self.screen_shake.get_offset()

        self.draw_background()
        self.draw_court(offset)

        # パーティクル
        for p in self.particles:
            p.draw(screen, offset)

        # ゲームオブジェクト
        self.player1.draw(screen, offset)
        self.player2.draw(screen, offset)
        self.ball.draw(screen, offset)

        # ポップアップ
        for p in self.popups:
            p.draw(screen, offset)

        self.draw_hud(offset)

        if self.paused:
            self.draw_pause_overlay(offset)
        elif self.game_over:
            self.draw_game_over(offset)

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "playing":
                            self.state = "menu"
                            self.reset()
                        else:
                            running = False
                    elif event.key == pygame.K_SPACE:
                        if self.state == "menu":
                            self.state = "playing"
                            self.reset()
                        elif not self.game_over:
                            self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        if self.state == "playing":
                            self.reset()

            if self.state == "playing":
                self.handle_input()
            self.update()
            self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
