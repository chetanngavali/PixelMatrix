"""
PixelMatrix Screen Sync Desktop Application Entry Point
Developed by Chetan Ngavali (@chetanngavali).
"""

import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from desktop.ui.main_window import ScreenSyncApp

def main():
    print("============================================================")
    print("  PixelMatrix Dynamic Screen Sync Ambilight")
    print("  Developed by Chetan Ngavali (@chetanngavali)")
    print("============================================================")
    app = ScreenSyncApp()
    app.mainloop()

if __name__ == "__main__":
    main()
