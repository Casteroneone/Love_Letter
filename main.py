"""
main.py
Entry point for the Love Letter game.
Run this file to start the game:
    python main.py
"""

import sys
import os

# Ensure the project root is on the path (supports running from any directory)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from love_letter.gui import App


def main():
    try:
        app = App()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
