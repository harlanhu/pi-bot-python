import time
from lib.enums import DevicesIdEnums, GpioBmcEnums, Constants
from core.gpio import GPIO


class DeviceManager:
    """
    设备管理器
    """

    def __init__(self, devices_dict=None):
        if devices_dict is None:
            devices_dict = dict()
        self.devices_dict = devices_dict
        self.setup()

    def setup(self):
        default_buzzer = self.devices_dict.get(DevicesIdEnums.DEFAULT_BUZZER)  # type:Buzzer
        default_buzzer.on()

    def get_devices(self):
        return self.devices_dict

    def get_all_devices(self):
        return self.devices_dict.values()

    def get_all_device_id(self):
        return self.devices_dict.keys()

    def get_device(self, device_id):
        return self.devices_dict.get(device_id)

    def logoff_device(self, device_id):
        self.devices_dict.pop(device_id)

    def destroy(self):
        self.devices_dict = None

    def get_devices_num(self):
        return len(self.devices_dict)


class Buzzer:
    """
    蜂鸣器
    有源蜂鸣器: 高电平无声/低电平发声
    """
    def __init__(self, device_id, channel):
        self.device_id = device_id
        self.channel = channel
        GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)

    def on(self, duration=0.2):
        GPIO.output(self.channel, GPIO.LOW)
        time.sleep(duration)
        GPIO.output(self.channel, GPIO.HIGH)

    def loop(self, duration=0.2, loop=1):
        for i in range(loop):
            self.on(duration)

    def cycle(self, duration=0.2, loop=3, interval=0.5, cycle=1):
        for i in range(cycle):
            self.loop(duration, loop)
            time.sleep(interval)

    def off(self):
        GPIO.setup(self.channel, GPIO.HIGH)


class Smog:

    def __init__(self, device_id, do_channel, mode):
        self.device_id = device_id
        self.do_channel = do_channel
        self.mode = mode
        if mode == Constants.DO_TYPE:
            GPIO.setup(do_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def has_smoke(self):
        if self.mode == Constants.DO_TYPE:
            return not GPIO.input(self.do_channel)


class Thermometer:

    def __init__(self, device_id, channel):
        self.device_id = device_id
        self.channel = channel
        self.data = []
        # 上电后延迟1s，排除传感器不稳定状态
        time.sleep(1)