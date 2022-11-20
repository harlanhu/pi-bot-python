from core import gpio
from core.base import FunctionManager
import pydevd_pycharm

pydevd_pycharm.settrace('192.168.31.229', port=19800, stdoutToServer=True, stderrToServer=True)


pi_bot = None

if __name__ == '__main__':
    try:
        pi_bot = FunctionManager()
        pi_bot.smoke_detection()
        pi_bot.body_detection()
        pi_bot.oled_display_info()
    except KeyboardInterrupt:
        if pi_bot is not None:
            pi_bot.off()
        gpio.destroy()
