import game
import model

from config import *

if __name__ == "__main__":
    print("="*50)
    print("Debug message level")
    if CONFIG_DEBUG_MAIN >= 0:
        print("    Global:", CONFIG_DEBUG_MAIN)
    if CONFIG_DEBUG_INSTANCE >= 0:
        print("    Instance:", CONFIG_DEBUG_INSTANCE)
    print("="*50)
    print_config()
    print("="*50)
    g = game.Game()
    g.loop()

