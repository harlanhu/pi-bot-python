from core import gpio
from core.base import FunctionManager

pi_bot = None

if __name__ == '__main__':
    try:
        pi_bot = FunctionManager()
        pi_bot.smoke_detection()
        pi_bot.display_roll()
    except KeyboardInterrupt:
        if pi_bot is not None:
            pi_bot.off()
        gpio.destroy()
