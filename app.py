"""
Simple Crossy Road clone (block/pixel style) using Pygame.

How to run:
1. pip install pygame
2. python crossyroad.py
"""

import pygame
import random
import sys

# ---------- Config ----------
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 800
FPS = 60

LANE_COUNT = 5
LANE_HEIGHT = 80
TOP_MARGIN = 140  # space for top grass / status
BOTTOM_MARGIN = 140

GRASS_COLOR = (106, 190, 48)
ROAD_COLOR = (50, 50, 50)
LINE_COLOR = (140, 140, 140)
TREE_TRUNK = (90, 50, 20)
TREE_LEAVES = (40, 120, 30)
DUCK_COLOR = (255, 120, 200)   # pink duck
DUCK_BEAK = (255, 165, 0)
SCORE_COLOR = (255, 255, 255)

LANE_Y = []  # computed later

# Player parameters (grid-like step size)
STEP_X = 64
STEP_Y = LANE_HEIGHT  # jump per lane vertically
DUCK_SIZE = 40

# Vehicle presets (width, height)
VEHICLE_TYPES = [
    (60, 40),
    (100, 40),
    (140, 40),
    (40, 40)
]

# ---------- Initialization ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crossy Duck")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 36, bold=True)

# compute lane y positions (center of each lane)
usable_height = SCREEN_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
lane_spacing = usable_height / LANE_COUNT
for i in range(LANE_COUNT):
    # lane rectangle's top y
    y_top = TOP_MARGIN + int(i * lane_spacing)
    LANE_Y.append(y_top)

# ---------- Game objects ----------
class Vehicle:
    def __init__(self, x, y, w, h, speed, direction):
        self.rect = pygame.Rect(x, y, w, h)
        self.speed = speed  # pixels per second
        self.direction = direction  # 1 = right, -1 = left
        self.color = (
            random.randint(50, 240),
            random.randint(50, 240),
            random.randint(50, 240)
        )

    def update(self, dt):
        self.rect.x += int(self.direction * self.speed * dt)
    
    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)
        # simple windshield
        win_w = max(10, self.rect.width // 3)
        win_h = max(10, self.rect.height // 2)
        win_x = self.rect.centerx - win_w//2
        win_y = self.rect.y + 6
        pygame.draw.rect(surf, (20,20,20), (win_x, win_y, win_w, win_h))

class Player:
    def __init__(self):
        # start bottom-center on the grass
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 2 - DUCK_SIZE // 2
        self.y = SCREEN_HEIGHT - BOTTOM_MARGIN + (BOTTOM_MARGIN - DUCK_SIZE)//2
        self.rect = pygame.Rect(self.x, self.y, DUCK_SIZE, DUCK_SIZE)
        self.alive = True

    def draw(self, surf):
        # blocky duck (body)
        pygame.draw.rect(surf, DUCK_COLOR, self.rect)
        # beak
        beak = pygame.Rect(self.rect.right, self.rect.centery - 6, 12, 12)
        pygame.draw.rect(surf, DUCK_BEAK, beak)
        # eye (single pixel)
        pygame.draw.rect(surf, (0,0,0), (self.rect.x + 8, self.rect.y + 8, 6, 6))

    def move(self, dx, dy):
        # snap to grid steps (STEP_X, STEP_Y) while keeping on-screen
        new_x = self.rect.x + dx * STEP_X
        new_y = self.rect.y + dy * STEP_Y
        # constrain horizontally in screen
        max_x = SCREEN_WIDTH - DUCK_SIZE
        min_y = 0
        max_y = SCREEN_HEIGHT - DUCK_SIZE
        self.rect.x = max(0, min(new_x, max_x))
        self.rect.y = max(min_y, min(new_y, max_y))

# ---------- Spawn & lane management ----------
class LaneManager:
    def __init__(self):
        self.vehicles = []  # list per lane? we'll store all
        # For each lane define direction and base speed
        self.lane_info = []
        base_speeds = [140, 200, 120, 180, 160]  # base speeds per lane
        for i in range(LANE_COUNT):
            # randomize direction per lane
            dir_ = -1 if i % 2 == 0 else 1
            self.lane_info.append({
                "direction": dir_,
                "base_speed": base_speeds[i % len(base_speeds)],
                "spawn_timer": 0.0,
                "spawn_interval": random.uniform(0.9, 2.2)
            })

    def update(self, dt, difficulty_multiplier):
        # update vehicles
        for v in self.vehicles:
            v.update(dt)
        # remove off-screen vehicles
        self.vehicles = [v for v in self.vehicles if -200 < v.rect.x < SCREEN_WIDTH + 200]

        # spawn vehicles per lane
        for i in range(LANE_COUNT):
            info = self.lane_info[i]
            info["spawn_timer"] += dt
            # dynamic spawn interval affected by difficulty
            spawn_interval = max(0.4, info["spawn_interval"] / difficulty_multiplier)
            if info["spawn_timer"] >= spawn_interval:
                info["spawn_timer"] = 0.0
                # choose vehicle size
                w, h = random.choice(VEHICLE_TYPES)
                lane_y = LANE_Y[i] + (LANE_HEIGHT - h)//2
                direction = info["direction"]
                speed = info["base_speed"] * random.uniform(0.9, 1.3) * difficulty_multiplier
                # spawn off-screen depending on direction
                if direction == 1:
                    x = -w - random.randint(10, 200)
                else:
                    x = SCREEN_WIDTH + random.randint(10, 200)
                v = Vehicle(x, lane_y, w, h, speed, direction)
                self.vehicles.append(v)

    def draw(self, surf):
        for v in self.vehicles:
            v.draw(surf)

    def lane_rects(self):
        rects = []
        for i in range(LANE_COUNT):
            rects.append(pygame.Rect(0, LANE_Y[i], SCREEN_WIDTH, LANE_HEIGHT))
        return rects

# ---------- Game loop ----------
def draw_background(surf):
    # top grass
    pygame.draw.rect(surf, GRASS_COLOR, (0, 0, SCREEN_WIDTH, TOP_MARGIN))
    pygame.draw.rect(surf, GRASS_COLOR, (0, SCREEN_HEIGHT - BOTTOM_MARGIN, SCREEN_WIDTH, BOTTOM_MARGIN))

    # draw some stylized trees on top grass
    for i in range(5):
        tx = 40 + i * 120
        ty = 30
        pygame.draw.rect(surf, TREE_TRUNK, (tx + 12, ty + 30, 12, 24))
        pygame.draw.rect(surf, TREE_LEAVES, (tx, ty, 48, 40))

    # roads
    for i in range(LANE_COUNT):
        y = LANE_Y[i]
        pygame.draw.rect(surf, ROAD_COLOR, (0, y, SCREEN_WIDTH, LANE_HEIGHT))
        # dashed lines
        dash_w = 60
        dash_h = 8
        for x in range(0, SCREEN_WIDTH, 140):
            pygame.draw.rect(surf, LINE_COLOR, (x + 20, y + LANE_HEIGHT//2 - dash_h//2, dash_w, dash_h))

def display_text(surf, text, pos, fontobj, color=(255,255,255)):
    surf.blit(fontobj.render(text, True, color), pos)

def main():
    player = Player()
    lanes = LaneManager()

    score = 0
    high_score = 0
    best_cross_y = player.rect.y  # track how far up the player reached
    difficulty = 1.0

    running = True
    paused = False
    last_time = pygame.time.get_ticks() / 1000.0

    while running:
        # dt in seconds
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now
        if dt > 0.05:
            dt = 0.05  # clamp large dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p:
                    paused = not paused
                if player.alive and not paused:
                    if event.key == pygame.K_UP:
                        player.move(0, -1)
                    elif event.key == pygame.K_DOWN:
                        player.move(0, 1)
                    elif event.key == pygame.K_LEFT:
                        player.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        player.move(1, 0)
                elif not player.alive:
                    # press space to restart
                    if event.key == pygame.K_SPACE:
                        player.reset()
                        lanes.vehicles.clear()
                        if score > high_score:
                            high_score = score
                        score = 0
                        best_cross_y = player.rect.y
                        difficulty = 1.0

        if not paused and player.alive:
            # difficulty increases with score
            difficulty = 1.0 + score * 0.08
            lanes.update(dt, difficulty)

            # collision check (only when on road)
            for v in lanes.vehicles:
                if player.rect.colliderect(v.rect):
                    player.alive = False
                    break

            # check if player progressed higher than before
            if player.rect.y < best_cross_y:
                # how many lanes crossed? Each lane height is STEP_Y; we can update score when crossing a lane boundary
                # We'll add +1 per lane crossed beyond previous best
                dist_crossed = int((best_cross_y - player.rect.y) / STEP_Y)
                if dist_crossed > 0:
                    score += dist_crossed
                    best_cross_y = player.rect.y

            # if player reaches very top (past top grass), award big bonus and reset to bottom
            if player.rect.y <= 10:
                # successful crossing
                score += 5
                # reset to bottom for next run, but keep difficulty
                player.reset()
                best_cross_y = player.rect.y

        # ---------- draw ----------
        screen.fill((0, 0, 0))
        draw_background(screen)

        # draw lanes & vehicles
        lanes.draw(screen)

        # draw player
        player.draw(screen)

        # HUD
        display_text(screen, f"Score: {score}", (16, 14), font, SCORE_COLOR)
        display_text(screen, f"High: {high_score}", (SCREEN_WIDTH - 140, 14), font, SCORE_COLOR)
        display_text(screen, "Use arrow keys to move. SPACE to restart after death. P to pause.", (16, SCREEN_HEIGHT - 34), font, SCORE_COLOR)

        if paused:
            display_text(screen, "PAUSED", (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2), big_font, (255, 220, 60))

        if not player.alive:
            # draw dead overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0,0))
            display_text(screen, "You Died!", (SCREEN_WIDTH//2 - 70, SCREEN_HEIGHT//2 - 30), big_font, (255, 80, 80))
            display_text(screen, f"Final Score: {score}", (SCREEN_WIDTH//2 - 90, SCREEN_HEIGHT//2 + 8), font, (255,255,255))
            display_text(screen, "Press SPACE to restart", (SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 48), font, (200,200,200))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
