from core import gpio
from core.base import Bot

pi_bot = None

if __name__ == '__main__':
    try:
        pi_bot = Bot()
        pi_bot.smoke_detection()
    except KeyboardInterrupt:
        if pi_bot is not None:
            pi_bot.off()
        gpio.destroy()
