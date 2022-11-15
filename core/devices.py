import time
from lib.enums import DevicesIdEnums, Constants, GpioBmcEnums

from core.gpio import GPIO


class Device:

    def __init__(self, device_id):
        self.device_id = device_id


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
        default_nixie_tube = self.devices_dict.get(DevicesIdEnums.DEFAULT_NIXIE_TUBE)  # type:NixieTube
        default_nixie_tube.on()

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


class Buzzer(Device):
    """
    蜂鸣器
    有源蜂鸣器: 高电平无声/低电平发声
    """

    def __init__(self, device_id, channel):
        super().__init__(device_id)
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


class Smog(Device):

    def __init__(self, device_id, do_channel, mode):
        super().__init__(device_id)
        self.do_channel = do_channel
        self.mode = mode
        if mode == Constants.DO_TYPE:
            GPIO.setup(do_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def has_smoke(self):
        if self.mode == Constants.DO_TYPE:
            return not GPIO.input(self.do_channel)


class Thermometer(Device):

    def __init__(self, device_id, channel):
        super().__init__(device_id)
        self.channel = channel
        self.data = []
        # 上电后延迟1s，排除传感器不稳定状态
        time.sleep(1)


# 数码管
class NixieTube(Device):
    """
    1，2，3，4 gpio控制第几个数字发光，dp控制点
    a-g 控制显示内容
    """
    zero = [0, 0, 0, 0, 0, 0, 1, 1]
    one = [1, 0, 0, 1, 1, 1, 1, 1]
    two = [0, 0, 1, 0, 0, 1, 0, 1]
    three = [0, 0, 0, 0, 1, 1, 0, 1]
    four = [1, 0, 0, 1, 1, 0, 0, 1]
    five = [0, 1, 0, 0, 1, 0, 0, 1]
    six = [0, 1, 0, 0, 0, 0, 0, 1]
    seven = [0, 0, 0, 1, 1, 1, 1, 1]
    eight = [0, 0, 0, 0, 0, 0, 0, 1]
    nine = [0, 0, 0, 0, 1, 0, 0, 1]

    refresh_time = 0.0005

    def __init__(self, device_id, channel_1, channel_2, channel_3, channel_4,
                 channel_a, channel_b, channel_c, channel_d, channel_e, channel_f, channel_g, channel_dp):
        super().__init__(device_id)
        self.sequence = [channel_4, channel_3, channel_2, channel_1]
        self.channels = [channel_a, channel_b, channel_c, channel_d,
                         channel_e, channel_f, channel_g, channel_dp]
        self.all_channels = [channel_1, channel_2, channel_3, channel_4,
                             channel_a, channel_b, channel_c, channel_d,
                             channel_e, channel_f, channel_g, channel_dp]
        GPIO.setup(self.all_channels, GPIO.OUT)
        GPIO.output(self.all_channels, GPIO.LOW)

    def on(self):
        stat_time = time.time()
        while time.time() - stat_time < 1:
            for seq in range(4):
                self.show_digit(seq, 8)
                time.sleep(self.refresh_time)
        GPIO.output(self.all_channels, GPIO.LOW)

    def show_digit(self, sequence, num):
        # 先将负极拉低，关掉显示
        GPIO.output(self.sequence, GPIO.LOW)
        channels = []
        if num == 0:
            channels = self.zero
        elif num == 1:
            channels = self.one
        elif num == 2:
            channels = self.two
        elif num == 3:
            channels = self.three
        elif num == 4:
            channels = self.four
        elif num == 5:
            channels = self.five
        elif num == 6:
            channels = self.six
        elif num == 7:
            channels = self.seven
        elif num == 8:
            channels = self.eight
        elif num == 9:
            channels = self.nine
        GPIO.output(self.channels, channels)
        GPIO.output(self.sequence[sequence], GPIO.HIGH)
