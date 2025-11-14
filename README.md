# Thru' The Wall (Pygame Conversion)

Summary
- A Pygame conversion of an old ZX Spectrum BASIC game "Thru' The Wall".
- Ball-and-paddle gameplay with a Spectrum-inspired color palette and simplified physics.

Dependencies
- Python 3.8+
- pygame

Install
- On Debian/Ubuntu:
  sudo apt install python3-pip
  pip install pygame

Run
- From the project root:
  python3 ThruTheWall.py

Controls
- O: move paddle left (hold Shift+O to move by 2)
- P: move paddle right (hold Shift+P to move by 2)
- Title screen: press any key to start
- Game over: press Y to restart, N to quit

Notes
- Direction magic numbers are now named constants (D_DOWN_RIGHT, D_UP_RIGHT, ...).
- Globals mirror the original BASIC program; consider refactoring into a GameState object.
- The code contains comments referencing original BASIC line groupings and behavior.