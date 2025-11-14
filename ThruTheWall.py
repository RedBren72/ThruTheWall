# Thru' The Wall (Pygame conversion)
#
# This file is a lightly refactored and documented port of a ZX Spectrum BASIC
# game to Pygame. The original program used many global variables and GOTO/GOSUB
# flow; this retains that flavor but adds docstrings, comments, and named
# constants for direction magic numbers.
#
# Minimal logic changes:
# - Introduced named direction constants and a `canonical` helper to map variant
#   codes to canonical directions. This keeps behavior identical while making
#   conditions readable.
# - Fixed missing `global tt` in game_over (was causing UnboundLocalError).
#
# Suggested future work: convert globals into a GameState dataclass.

import pygame
import random
import sys

# --- Pygame Setup ---
pygame.init()

# Constants for the original game's screen/grid size
# ZX Spectrum screen is 32 columns x 24 rows (approx)
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Thru' The Wall (Pygame Conversion)")

# Colors (Approximating Spectrum colors)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
CYAN = (0, 200, 200)
YELLOW = (200, 200, 0)

FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 24)

# --- Direction constants (replace magic numbers used in the BASIC port) ---
# The original BASIC used values such as 100,106,120,125,... to encode
# movement routines/directions. We keep those integer values but expose
# canonical names for readability and a mapping for variant codes.
D_DOWN_RIGHT = 100
D_UP_RIGHT = 120
D_UP_LEFT = 140
D_DOWN_LEFT = 160
D_UP = 180
D_DOWN = 200

# Some BASIC variants used near-duplicates like 106, 125, 145, 166, 206.
# Map those to canonical directions for easier checks.
_VARIANT_TO_CANON = {
    106: D_DOWN_RIGHT,
    125: D_UP_RIGHT,
    145: D_UP_LEFT,
    166: D_DOWN_LEFT,
    206: D_DOWN,
}

def canonical(g):
    """Return canonical direction integer for potentially-variant code g."""
    return _VARIANT_TO_CANON.get(g, g)

# --- Global Game Variables (from BASIC) ---
tt = -1  # Total games counter (Line 10)
t = 0    # Score counter (Line 250)
a = 13   # Paddle position (x-coordinate, BASIC 'a')
w = 0    # Wall break flag (Line 112,132,152,172)
g = D_DOWN  # Current movement routine index (direction)
r = 0    # Current round (Line 50)
score = 0
running = True

# Convert BASIC grid coordinates to Pygame pixel coordinates
def to_pixels(x, y):
    """Convert BASIC-like grid coords to screen pixel center coords.

    The original BASIC code uses grid columns/rows; this maps a grid cell to
    a pixel center. Note: many calls use (n, m) ordering; the function is
    intentionally simple and mirrors the original usage.
    """
    return x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2

# --- Drawing Functions ---

def draw_background():
    """Render static background elements (paper, wall area, play boundary)."""
    SCREEN.fill(WHITE)  # PAPER 7 in the BASIC port
    # Draw the 'Wall' region (simulating BASIC lines 30-40)
    pygame.draw.rect(SCREEN, CYAN, (0, 0, SCREEN_WIDTH, 120))
    # Draw the play area boundary (frame)
    pygame.draw.rect(SCREEN, BLACK, (0, 0, SCREEN_WIDTH, 420), 2)

def draw_paddle(x):
    """Draw the paddle at BASIC paddle position `x`.

    Paddle 'a' is an integer roughly in 1..28; we scale it by GRID_SIZE.
    """
    paddle_y = 21  # BASIC line ~21
    x_pos = x * GRID_SIZE
    paddle_width = 4 * GRID_SIZE
    paddle_height = GRID_SIZE
    pygame.draw.rect(SCREEN, BLUE, (x_pos, paddle_y * GRID_SIZE, paddle_width, paddle_height))

def draw_ball(m, n):
    """Draw the ball at BASIC coordinates (m, n)."""
    x, y = to_pixels(n, m)  # note ordering preserved from original code
    pygame.draw.circle(SCREEN, RED, (x, y), GRID_SIZE // 3)

def draw_status():
    """Render score and round status at the bottom of the screen."""
    global t, tt
    current_score = tt * 600 + t  # scoring formula carried from BASIC
    score_text = FONT.render(f"SCORE: {current_score}", True, BLACK)
    round_text = FONT.render(f"ROUND: {r}", True, BLACK)
    SCREEN.blit(score_text, (20, SCREEN_HEIGHT - 50))
    SCREEN.blit(round_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50))

# --- Movement/Collision Logic (Based on GOTO/GOSUB) ---

def move_ball(m, n, g):
    """Return new (m, n) after moving the ball according to direction `g`.

    The direction is canonicalized to support the BASIC variant codes.
    """
    cg = canonical(g)

    # Down-Right
    if cg == D_DOWN_RIGHT:
        m += 1
        n += 1
    # Up-Right
    elif cg == D_UP_RIGHT:
        m -= 1
        n += 1
    # Up-Left
    elif cg == D_UP_LEFT:
        m -= 1
        n -= 1
    # Down-Left
    elif cg == D_DOWN_LEFT:
        m += 1
        n -= 1
    # Up
    elif cg == D_UP:
        m -= 1
    # Down
    elif cg == D_DOWN:
        m += 1

    return m, n

def check_boundaries(m, n, g, w):
    """Adjust direction `g` when the ball hits screen boundaries.

    Behavior mirrors BASIC checks:
    - If n > 30 and ball moving right, flip to move left.
    - If n < 1 and ball moving left, flip to move right.
    - If m < 1 (top) and moving upward, send the ball down.
    `w` is the wall-break flag kept for parity with the BASIC logic.
    """
    cg = canonical(g)

    # Right wall: if column n goes past ~30 and was moving right -> go left
    if n > 30:
        if cg in (D_DOWN_RIGHT, D_UP_RIGHT):
            return D_DOWN_LEFT  # 160 in BASIC

    # Left wall: if column n < 1 and was moving left -> go right
    elif n < 1:
        if cg in (D_UP_LEFT, D_DOWN_LEFT):
            return D_DOWN_RIGHT  # 100 in BASIC

    # Top of screen: if m < 1 and was moving upward -> send down
    if m < 1:
        if cg in (D_UP_RIGHT, D_UP_LEFT, D_UP):
            # In the original, hitting some top-wall locations set w=1 and caused different
            # outcomes; here we simplify to a downward bounce.
            return D_DOWN

    return g

def check_paddle_collision(m, n, a, g):
    """Detect paddle hit and return updated direction `g`.

    If the ball strikes the paddle row (m == 20) and column is within
    paddle span [a, a+3], score `t` is incremented and direction is changed
    based on the hit position (left/center/right).
    """
    global t, tt
    if m == 20:
        if a <= n <= a + 3:
            t += 10  # BASIC Line 250: score increment
            # Determine new direction based on where on paddle the ball hit
            if n == a or n == a + 1:
                return D_UP_LEFT   # favor left rebound
            elif n == a + 2:
                return D_UP        # straight up
            elif n == a + 3 or n == a + 4:
                return D_UP_RIGHT  # favor right rebound
    return g

# --- Game Loops ---

def game_over():
    """Handle end-of-game UI and wait for restart/exit decision.

    Displays final score and listens for Y (restart) or N (exit).
    """
    global running, tt  # tt is modified here
    tt += 1  # increment total games counter (BASIC Line 240)

    SCREEN.fill(BLACK)
    final_score = tt * 600 + t

    game_over_text = FONT.render("GAME OVER", True, WHITE)
    score_display = FONT.render(f"FINAL SCORE: {final_score}", True, WHITE)
    replay_text = SMALL_FONT.render("Press 'Y' to play again, 'N' to exit", True, WHITE)

    SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3))
    SCREEN.blit(score_display, (SCREEN_WIDTH // 2 - score_display.get_width() // 2, SCREEN_HEIGHT // 3 + 50))
    SCREEN.blit(replay_text, (SCREEN_WIDTH // 2 - replay_text.get_width() // 2, SCREEN_HEIGHT // 3 + 150))
    pygame.display.flip()

    # Wait for user decision
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    # Restart the main game loop
                    main_game_loop()
                elif event.key == pygame.K_n:
                    running = False
                    return

def main_game_loop():
    """Run the main gameplay loop: rounds, paddle control, ball movement, drawing."""
    global tt, t, a, w, g, r, running

    tt += 1
    t = 0

    # Outer loop: FOR r = 1 TO 6 in the BASIC original
    for r in range(1, 7):
        # Initialize ball and paddle for this round
        m = 10
        n = 8 + random.randint(0, 13)
        g = D_DOWN
        a = 13
        w = 0

        # Inner loop: while the ball hasn't passed the paddle row (m <= 20)
        while m <= 20:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # --- Input Handling (Lines 80-86 in BASIC mapping) ---
            keys = pygame.key.get_pressed()
            # 'o' (K_o): Move Left by 1
            if keys[pygame.K_o] and a > 1:
                a -= 1
            # Shift + 'o': Move left faster by 2
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and keys[pygame.K_o] and a > 2:
                a -= 2
            # 'p': Move Right by 1
            if keys[pygame.K_p] and a < 28:
                a += 1
            # Shift + 'p': Move right faster by 2
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and keys[pygame.K_p] and a < 27:
                a += 2

            # --- Movement and Collision ---
            g = check_paddle_collision(m, n, a, g)
            g = check_boundaries(m, n, g, w)
            m, n = move_ball(m, n, g)

            # --- Drawing ---
            draw_background()
            draw_paddle(a)
            draw_ball(m, n)
            draw_status()
            pygame.display.flip()

            # Speed control (approx 20 frames/sec)
            pygame.time.Clock().tick(20)

        # Ball missed the paddle -> exit inner loop to handle game over
        break

    # If the FOR loop completes (r == 6), the player won all rounds (message only)
    if r == 6:
        print("You WON the 6 rounds!")

    game_over()

# --- Title Screen (Lines 310-530 mapping) ---
def title_screen():
    """Show title and wait for any key to start the game."""
    SCREEN.fill(WHITE)

    title_text = FONT.render("THRO' THE WALL (Pygame)", True, BLUE)
    instructions = SMALL_FONT.render("O/P to move left/right", True, BLACK)
    zip_text = SMALL_FONT.render("CAPS SHIFT for extra zip", True, BLACK)
    start_text = FONT.render("PRESS ANY KEY TO START", True, RED)

    SCREEN.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
    SCREEN.blit(instructions, (50, 200))
    SCREEN.blit(zip_text, (50, 250))
    SCREEN.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 400))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

    main_game_loop()

# Entry point
title_screen()

# Final exit cleanup
if not running:
    pygame.quit()
    sys.exit()