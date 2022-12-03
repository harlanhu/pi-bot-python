from core import gpio
from core.base import Bot
from core.devices import Buzzer, Smog, Thermometer, BodyInfraredSensor, OledDisplay, DeviceManager, PCF8591, Camera
from core.function import FunctionManager
from lib.enums import DevicesId, GpioBmcEnums, Constants


def init_devices():
    buzzer = Buzzer(DevicesId.DEFAULT_BUZZER, GpioBmcEnums.GPIO_7)
    smog = Smog(DevicesId.DEFAULT_SMOG, GpioBmcEnums.GPIO_11, Constants.DO_TYPE)
    thermometer = Thermometer(DevicesId.DEFAULT_THERMOMETER, GpioBmcEnums.GPIO_12)
    body_infrared_sensor = BodyInfraredSensor(DevicesId.DEFAULT_BODY_INFRARED_SENSOR, GpioBmcEnums.GPIO_13)
    oled_display = OledDisplay(DevicesId.DEFAULT_OLED_DISPLAY)
    pcf8591 = PCF8591(DevicesId.DEFAULT_PCF8591, 1, 0x48)
    camera = Camera(DevicesId.DEFAULT_CAMERA, GpioBmcEnums.GPIO_15)
    return {
        buzzer.device_id: buzzer,
        smog.device_id: smog,
        thermometer.device_id: thermometer,
        body_infrared_sensor.device_id: body_infrared_sensor,
        oled_display.device_id: oled_display,
        pcf8591.device_id: pcf8591,
        camera.device_id: camera
    }


pi_bot = None

if __name__ == '__main__':
    try:
        print('正在注册设备中...')
        device_manager = DeviceManager(init_devices())
        print('正在初始化功能...')
        function_manager = FunctionManager()
        print('正在初始化机器人...')
        pi_bot = Bot(None, device_manager, function_manager)
        print('正在启动功能...')
        pi_bot.on()
        print('机器人已就绪')
    except KeyboardInterrupt:
        if pi_bot is not None:
            pi_bot.destroy()
        gpio.destroy()
