from core import gpio
import pydevd_pycharm

from core.base import Bot
from core.devices import Buzzer, Smog, Thermometer, BodyInfraredSensor, OledDisplay, DeviceManager
from core.function import FunctionManager
from lib.enums import DevicesIdEnums, GpioBmcEnums, Constants


# pydevd_pycharm.settrace('192.168.31.229', port=19800, stdoutToServer=True, stderrToServer=True)

def init_devices():
    buzzer = Buzzer(DevicesIdEnums.DEFAULT_BUZZER, GpioBmcEnums.GPIO_7)
    smog = Smog(DevicesIdEnums.DEFAULT_SMOG, GpioBmcEnums.GPIO_11, Constants.DO_TYPE)
    thermometer = Thermometer(DevicesIdEnums.DEFAULT_THERMOMETER, GpioBmcEnums.GPIO_12)
    body_infrared_sensor = BodyInfraredSensor(DevicesIdEnums.DEFAULT_BODY_INFRARED_SENSOR, GpioBmcEnums.GPIO_13)
    oled_display = OledDisplay(DevicesIdEnums.DEFAULT_OLED_DISPLAY)
    return {
        buzzer.device_id: buzzer,
        smog.device_id: smog,
        thermometer.device_id: thermometer,
        body_infrared_sensor.device_id: body_infrared_sensor,
        oled_display.device_id: oled_display
    }


pi_bot = None

if __name__ == '__main__':
    try:
        device_manager = DeviceManager(init_devices())
        function_manager = FunctionManager()
        pi_bot = Bot(None, device_manager, function_manager)
    except KeyboardInterrupt:
        if pi_bot is not None:
            pi_bot.destroy()
        gpio.destroy()
