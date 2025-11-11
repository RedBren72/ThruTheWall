import pygame
import random
import sys

# --- Pygame Setup ---
pygame.init()

# Constants for the original game's screen/grid size
# ZX Spectrum screen is 32 columns x 24 rows
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

# --- Global Game Variables (from BASIC) ---
tt = -1 # Total games counter (Line 10)
t = 0   # Score counter (Line 250)
a = 13  # Paddle position (x-coordinate, scaled)
w = 0   # Wall break flag (Line 112, 132, 152, 172)
g = 200 # Current movement routine index (direction)
r = 0   # Current round (Line 50)
score = 0
running = True

# Convert BASIC grid coordinates to Pygame pixel coordinates
def to_pixels(x, y):
    # n (0-31), m (1-21) -> screen pixels
    return x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2

# --- Drawing Functions ---

# Simulates the initial screen border and paper/ink setup
def draw_background():
    SCREEN.fill(WHITE) # PAPER 7
    # Draw the 'Wall' (Lines 30-40, simulated as a simple rect)
    pygame.draw.rect(SCREEN, CYAN, (0, 0, SCREEN_WIDTH, 120))
    # Draw the play area boundary
    pygame.draw.rect(SCREEN, BLACK, (0, 0, SCREEN_WIDTH, 420), 2)
    
# Draw the paddle (Lines 220-236 logic)
def draw_paddle(x):
    # Paddle is at line 21, positions 'a' (1-28)
    paddle_y = 21
    # Scale x (a) from 1-28 to the screen width
    x_pos = x * GRID_SIZE
    
    # Paddle width is 4 or 5 characters
    paddle_width = 4 * GRID_SIZE
    paddle_height = GRID_SIZE
    
    pygame.draw.rect(SCREEN, BLUE, (x_pos, paddle_y * GRID_SIZE, paddle_width, paddle_height))

# Draw the ball (Line 70)
def draw_ball(m, n):
    x, y = to_pixels(n, m)
    pygame.draw.circle(SCREEN, RED, (x, y), GRID_SIZE // 3)

# Display score/status (Line 244 logic)
def draw_status():
    global t, tt
    # Calculate score as in BASIC: tt*600 + t
    current_score = tt * 600 + t
    score_text = FONT.render(f"SCORE: {current_score}", True, BLACK)
    round_text = FONT.render(f"ROUND: {r}", True, BLACK)
    SCREEN.blit(score_text, (20, SCREEN_HEIGHT - 50))
    SCREEN.blit(round_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50))
    
# --- Movement/Collision Logic (Based on GOTO/GOSUB) ---

# Core movement function
def move_ball(m, n, g):
    # Line 110: Move Down-Right (g=100)
    if g == 100 or g == 106:
        m += 1
        n += 1
    # Line 130: Move Up-Right (g=120)
    elif g == 120 or g == 125:
        m -= 1
        n += 1
    # Line 150: Move Up-Left (g=140)
    elif g == 140 or g == 145:
        m -= 1
        n -= 1
    # Line 170: Move Down-Left (g=160)
    elif g == 160 or g == 166:
        m += 1
        n -= 1
    # Line 190: Move Up (g=180)
    elif g == 180:
        m -= 1
    # Line 212: Move Down (g=200)
    elif g == 200 or g == 206:
        m += 1
        
    return m, n

# Simplified Wall/Screen Boundary Check (Lines 106, 125, 140, 145, 166)
def check_boundaries(m, n, g, w):
    # Max x is approx 30 (Line 106: IF n>30 THEN LET g=160: GO TO 160)
    if n > 30: 
        if g in [100, 120]: # Hitting right wall
            return 160 # Change to move Left
    # Min x is approx 1 (Line 166: IF n<1 THEN LET g=100: GO TO 100)
    elif n < 1: 
        if g in [140, 160]: # Hitting left wall
            return 100 # Change to move Right
            
    # Hitting the top of the screen (Line 125, 140, 180)
    # The original game has complex wall collision ATTR (m,n), 
    # we'll simplify to just the top edge for now (m < 1)
    if m < 1:
        if g in [120, 140, 180]: # Hitting top
            # Wall break logic (w=1, Line 125, 140)
            return 200 # Change to move Down (200 is DOWN)
    
    return g

# Paddle Collision Check (Lines 103-105, 163-165, 204-210)
def check_paddle_collision(m, n, a, g):
    global t, tt
    
    if m == 20: # Ball is at paddle height
        # Simplified hit detection: Check if n is within the paddle's x range [a, a+3]
        if a <= n <= a + 3: 
            t += 10 # Score increment (Line 250)
            
            # The original BASIC changes direction based on WHERE on the paddle it hits (n vs a)
            
            # Hit far left (n=a-1/a) -> g=140 (Up-Left)
            if n == a or n == a + 1: 
                return 140
            # Hit center (n=a+2) -> g=180 (Up)
            elif n == a + 2:
                return 180
            # Hit far right (n=a+3/a+4) -> g=120 (Up-Right)
            elif n == a + 3 or n == a + 4:
                return 120
            
    return g

# --- Game Loops ---

def game_over():
    global running
    tt += 1 # Game over, increment game count
    
    # Line 240: BEEP .02,20-a: NEXT a: BEEP .1,-20 (Simulated with pygame sound if desired)
    
    SCREEN.fill(BLACK)
    final_score = tt * 600 + t
    
    # Display end-game text (Line 244)
    game_over_text = FONT.render("GAME OVER", True, WHITE)
    score_display = FONT.render(f"FINAL SCORE: {final_score}", True, WHITE)
    replay_text = SMALL_FONT.render("Press 'Y' to play again, 'N' to exit", True, WHITE)
    
    SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3))
    SCREEN.blit(score_display, (SCREEN_WIDTH // 2 - score_display.get_width() // 2, SCREEN_HEIGHT // 3 + 50))
    SCREEN.blit(replay_text, (SCREEN_WIDTH // 2 - replay_text.get_width() // 2, SCREEN_HEIGHT // 3 + 150))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    # RUN (restart) - Line 246
                    main_game_loop()
                elif event.key == pygame.K_n:
                    # GO TO 8000 (exit) - Line 247/248
                    running = False
                    return

def main_game_loop():
    global tt, t, a, w, g, r, running
    
    tt += 1
    t = 0
    
    # Outer Loop: FOR r=1 TO 6 (Lines 50-242)
    for r in range(1, 7):
        m = 10 
        n = 8 + random.randint(0, 13)
        g = 200 # Start moving down
        a = 13  
        w = 0
        
        # Inner Loop: GO TO 60 / While m <= 20
        while m <= 20: 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            # --- Input Handling (Lines 80-86) ---
            keys = pygame.key.get_pressed()
            # 'o' (K_o): Move Left by 1 (GO SUB 220)
            if keys[pygame.K_o] and a > 1:
                a -= 1
            # 'O' (K_LSHIFT + K_o): Move Left by 2 (GO SUB 224)
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and keys[pygame.K_o] and a > 2:
                a -= 2
            # 'p' (K_p): Move Right by 1 (GO SUB 230)
            if keys[pygame.K_p] and a < 28:
                a += 1
            # 'P' (K_LSHIFT + K_p): Move Right by 2 (GO SUB 234)
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and keys[pygame.K_p] and a < 27:
                a += 2
                
            # --- Movement and Collision ---
            
            # 1. Check for Paddle Collision (m=20)
            g = check_paddle_collision(m, n, a, g)
            
            # 2. Check for Boundary Collision (m, n)
            g = check_boundaries(m, n, g, w)

            # 3. Move the ball
            m, n = move_ball(m, n, g)
            
            # 4. Drawing
            draw_background()
            draw_paddle(a)
            draw_ball(m, n)
            draw_status()
            pygame.display.flip()
            
            # Speed control (PAUSE 1 / Line 80)
            pygame.time.Clock().tick(20) # Approx 20 frames/sec

        # Ball missed the paddle (m > 20) - GO TO 240
        break # End the inner loop and move to game_over

    # If the FOR loop completes (r=1 to 6), the player won the round/game
    if r == 6:
        print("You WON the 6 rounds!")

    # End of the game/rounds loop
    game_over()


# --- Title Screen (Lines 310-530) ---
def title_screen():
    SCREEN.fill(WHITE)
    
    # Print titles and instructions (simulated GO SUB 3000)
    title_text = FONT.render("THRO' THE WALL (Pygame)", True, BLUE)
    instructions = SMALL_FONT.render("O/P to move left/right", True, BLACK)
    zip_text = SMALL_FONT.render("CAPS SHIFT for extra zip", True, BLACK)
    start_text = FONT.render("PRESS ANY KEY TO START", True, RED)
    
    SCREEN.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
    SCREEN.blit(instructions, (50, 200))
    SCREEN.blit(zip_text, (50, 250))
    SCREEN.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 400))
    pygame.display.flip()
    
    # PAUSE 0: RUN (Line 530)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

    main_game_loop()

# Start the game
title_screen()

# Final exit cleanup
if not running:
    pygame.quit()
    sys.exit()

