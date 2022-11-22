from core import gpio
import pydevd_pycharm
from core.function import FunctionManager

# pydevd_pycharm.settrace('192.168.31.229', port=19800, stdoutToServer=True, stderrToServer=True)


pi_bot = None

if __name__ == '__main__':
    try:
        pi_bot = FunctionManager()
        pi_bot.thermometer_detection()
        pi_bot.smoke_detection()
        pi_bot.body_detection()
        pi_bot.oled_display_info()
    except KeyboardInterrupt:
        if pi_bot is not None:
            pi_bot.stop_all()
        gpio.destroy()
