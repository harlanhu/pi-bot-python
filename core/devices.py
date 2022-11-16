import datetime
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

       __A__
      |     |    |  0 ->  011 1111 -> 0x3f
    F |     | B  |  1 ->  010 0001 -> 0x21
      |__G__|    |  2 ->  111 0110 -> 0x76
      |     |    |  4 ->  ...
    E |     | C  |        ...
      |__D__| DP |  9 ->  ...      -> 0x5f

    """

    alphabet = {
        '0': [0, 0, 0, 0, 0, 0, 1, 1],
        '1': [1, 0, 0, 1, 1, 1, 1, 1],
        '2': [0, 0, 1, 0, 0, 1, 0, 1],
        '3': [0, 0, 0, 0, 1, 1, 0, 1],
        '4': [1, 0, 0, 1, 1, 0, 0, 1],
        '5': [0, 1, 0, 0, 1, 0, 0, 1],
        '6': [0, 1, 0, 0, 0, 0, 0, 1],
        '7': [0, 0, 0, 1, 1, 1, 1, 1],
        '8': [0, 0, 0, 0, 0, 0, 0, 1],
        '9': [0, 0, 0, 0, 1, 0, 0, 1],
        'A': [0, 0, 0, 1, 0, 0, 0, 1],
        'B': [1, 1, 0, 0, 0, 0, 0, 1],
        'C': [0, 1, 1, 0, 0, 0, 1, 1],
        'D': [1, 0, 0, 0, 0, 1, 0, 1],
        'E': [0, 1, 1, 0, 0, 0, 0, 1],
        'F': [0, 1, 1, 1, 0, 0, 0, 1],
        'G': [0, 1, 0, 0, 0, 0, 1, 1],
        'H': [1, 0, 0, 1, 0, 0, 0, 1],
        'I': [0, 0, 0, 0, 1, 1, 1, 1],
        'J': [0, 1, 1, 1, 0, 0, 0, 1],
        'K': [0, 1, 0, 1, 0, 0, 0, 1],
        'L': [1, 1, 1, 0, 0, 0, 1, 1],
        'M': [0, 0, 0, 1, 0, 0, 1, 1],
        'N': [1, 1, 0, 1, 0, 1, 0, 1],
        'O': [1, 1, 0, 0, 0, 1, 0, 1],
        'P': [0, 0, 1, 1, 0, 0, 0, 1],
        'Q': [0, 0, 0, 1, 1, 0, 0, 1],
        'R': [0, 1, 1, 1, 0, 0, 1, 1],
        'S': [0, 1, 1, 0, 1, 1, 0, 1],
        'T': [1, 1, 1, 0, 0, 0, 0, 1],
        'U': [1, 0, 0, 0, 0, 0, 1, 1],
        'V': [1, 1, 0, 0, 0, 1, 1, 1],
        'W': [1, 0, 0, 0, 0, 0, 0, 1],
        'X': [1, 1, 0, 1, 1, 0, 0, 1],
        'Y': [1, 0, 0, 0, 1, 0, 0, 1],
        'Z': [1, 0, 1, 0, 0, 1, 0, 1],
        ' ': [1, 1, 1, 1, 1, 1, 1, 1],
        '-': [1, 1, 1, 1, 1, 1, 0, 1],
        '|': [1, 1, 1, 1, 0, 0, 1, 1]
    }

    refresh_time = 0.0005

    def __init__(self, device_id, channel_1, channel_2, channel_3, channel_4,
                 channel_a, channel_b, channel_c, channel_d, channel_e, channel_f, channel_g, channel_dp):
        super().__init__(device_id)
        self.sequence = [channel_1, channel_2, channel_3, channel_4]
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
                self.show_character(seq, 8)
                time.sleep(self.refresh_time)
        GPIO.output(self.all_channels, GPIO.LOW)

    def show_character(self, sequence, c, has_dot=False):
        # 先将负极拉低，关掉显示
        GPIO.output(self.sequence, GPIO.LOW)
        val = str(c)
        if not val.isnumeric():
            val = val.upper()
        states = self.alphabet.get(val)
        if states is None:
            return
        if has_dot:
            states[7] = 0
        GPIO.output(self.channels, states)
        GPIO.output(self.sequence[sequence], GPIO.HIGH)

    def display_content(self, content, interval=0):
        content_len = len(str(content))
        if interval == 0 and content_len > 4:
            interval = 0.7
        else:
            interval = 5.0
        if content_len > 4:
            self.display_long_str(content, interval)
        else:
            self.display_str(content, interval)

    def display_str(self, val, interval=5.0):
        val = str(val)
        start_time = time.time()
        while time.time() - start_time <= interval:
            for i in range(4):
                self.show_character(i, val[i])
                time.sleep(self.refresh_time)

    def display_long_str(self, val, interval=0.7):
        vals = '*' * 4 + str(val)
        fill_num = len(vals) % 4
        vals = vals + '*' * (fill_num + 4)
        dot_count = 0
        for i in range(0, len(vals) - 4):
            once_val = vals[i] + vals[i + 1] + vals[i + 2] + vals[i + 3]
            self.display_str(once_val, interval)

    def display_time(self, interval):
        stat_time = time.time()
        while time.time() - stat_time <= interval:
            now = datetime.datetime.now()
            hour = now.hour.numerator
            minute = now.minute.numerator
            time.sleep(self.refresh_time)
            self.show_character(0, int(hour / 10))
            time.sleep(self.refresh_time)
            self.show_character(1, hour % 10, True)
            time.sleep(self.refresh_time)
            self.show_character(2, int(minute / 10))
            time.sleep(self.refresh_time)
            self.show_character(3, minute % 10)

    def display_warning(self, interval, cycle):
        for i in range(cycle):
            self.display_str(8888, 0.3)
            time.sleep(interval)

