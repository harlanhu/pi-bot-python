import datetime
import threading
import time
from abc import abstractmethod, ABC

import numpy as np
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from lib.enums import DevicesIdEnums, Constants
from core.gpio import GPIO
import Adafruit_DHT
import simpleaudio as audio


class Device:

    def __init__(self, device_id):
        self.device_id = device_id
        self.lock = threading.RLock()

    @abstractmethod
    def setup(self):
        pass


class DeviceManager:
    """
    设备管理器
    """

    def __init__(self, devices_dict=None):
        if devices_dict is None:
            devices_dict = dict()
        self.devices_dict = devices_dict

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


class Buzzer(Device, ABC):
    """
    蜂鸣器
    有源蜂鸣器: 高电平无声/低电平发声
    """

    def __init__(self, device_id, channel):
        super().__init__(device_id)
        self.channel = channel
        GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)

    def setup(self):
        self.loop()

    def on(self):
        self.lock.acquire()
        GPIO.output(self.channel, GPIO.LOW)
        self.lock.release()

    def off(self):
        GPIO.output(self.channel, GPIO.HIGH)

    def play(self, duration=0.2):
        self.lock.acquire()
        GPIO.output(self.channel, GPIO.LOW)
        time.sleep(duration)
        GPIO.output(self.channel, GPIO.HIGH)
        self.lock.release()

    def loop(self, duration=0.2, loop=1):
        self.lock.acquire()
        for i in range(loop):
            self.play(duration)
        self.lock.release()

    def cycle(self, duration=0.2, loop=3, interval=0.5, cycle=1):
        self.lock.acquire()
        for i in range(cycle):
            self.loop(duration, loop)
            time.sleep(interval)
        self.lock.release()


class Smog(Device, ABC):

    def __init__(self, device_id, do_channel, mode):
        super().__init__(device_id)
        self.do_channel = do_channel
        self.mode = mode
        if mode == Constants.DO_TYPE:
            GPIO.setup(do_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def has_smoke(self):
        self.lock.acquire()
        if self.mode == Constants.DO_TYPE:
            return not GPIO.input(self.do_channel)
        self.lock.release()


class Thermometer(Device, ABC):

    def __init__(self, device_id, channel):
        super().__init__(device_id)
        self.channel = channel
        self.humidity = 0
        self.temperature = 0
        time.sleep(1)
        self.detection()

    def detection(self):
        self.humidity, self.temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, self.channel)
        return self.humidity, self.temperature


# 数码管
class NixieTube(Device, ABC):
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
        '|': [1, 1, 1, 1, 0, 0, 1, 1],
        '^': [1, 1, 1, 0, 0, 1, 0, 1],
        '%': [1, 1, 1, 1, 0, 1, 0, 1]
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

    def setup(self):
        stat_time = time.time()
        while time.time() - stat_time < 1:
            for seq in range(4):
                self.display_character(seq, 8)
                time.sleep(self.refresh_time)
        GPIO.output(self.all_channels, GPIO.LOW)

    def display_character(self, sequence, c, has_dot=False):
        # 先将负极拉低，关掉显示
        GPIO.output(self.all_channels, GPIO.LOW)
        GPIO.output(self.sequence, GPIO.LOW)
        val = str(c)
        if not val.isnumeric():
            val = val.upper()
        states = self.alphabet.get(val)
        if states is None:
            return
        if has_dot:
            states[7] = 0
        else:
            states[7] = 1
        GPIO.output(self.channels, states)
        GPIO.output(self.sequence[sequence], GPIO.HIGH)

    def display_refresh(self, sequence, c, has_dot=False):
        self.display_character(sequence, c, has_dot)
        time.sleep(self.refresh_time)

    def display_content(self, content, interval=0):
        content_len = len(str(content).replace('.', ''))
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
        no_dot_val = val.replace('.', '')
        fill_count = 4 - len(no_dot_val)
        val = val + '*' * fill_count
        val_mapping = [[], [], [], []]
        i = 0
        dot_count = 0
        while i < len(val):
            if dot_count >= 4:
                break
            if i < len(val) - 1 and val[i + 1] == '.':
                val_mapping[i - dot_count] = [val[i], True]
                dot_count += 1
                i += 2
            else:
                val_mapping[i - dot_count] = [val[i], False]
                i += 1
        self.display_val(val_mapping, interval)

    def display_val(self, val_mapping: list, interval=5.0):
        start_time = time.time()
        while time.time() - start_time <= interval:
            for i in range(4):
                self.display_refresh(i, val_mapping[i][0], val_mapping[i][1])
        GPIO.output(self.all_channels, GPIO.LOW)
        GPIO.output(self.sequence, GPIO.LOW)

    def display_long_str(self, val, interval=0.7):
        vals = '*' * 4 + str(val)
        fill_num = len(vals.replace('.', '')) % 4
        vals = vals + '*' * (fill_num + 4)
        i = 0
        while i < len(vals) - 4:
            val_mapping = [[], [], [], []]
            end_val_dot = False
            offset = 5
            if i % 4 != 0 or i != 0:
                offset = 4
            if (i + offset) < len(vals) and vals[i + offset] == '.':
                end_val_dot = True
            temp_val = vals[i: i + 4]
            dot_num = temp_val.count('.')
            temp_val = vals[i: i + 4 + dot_num]
            if temp_val[len(temp_val) - 1] == '.':
                temp_val = vals[i: i + 5 + dot_num]
            j = 0
            dot_count = 0
            while j < len(temp_val):
                if dot_count >= 4:
                    break
                if j < len(temp_val) - 1 and temp_val[j + 1] == '.':
                    val_mapping[j - dot_count] = [temp_val[j], True]
                    j += 2
                    dot_count += 1
                else:
                    val_mapping[j - dot_count] = [temp_val[j], False]
                    j += 1
            if end_val_dot:
                val_mapping[3][1] = True
            if val_mapping[0][1]:
                i += 2
            else:
                i += 1
            self.display_val(val_mapping, interval)
        GPIO.output(self.all_channels, GPIO.LOW)
        GPIO.output(self.sequence, GPIO.LOW)

    def display_time(self, interval):
        stat_time = time.time()
        while time.time() - stat_time <= interval:
            now = datetime.datetime.now()
            hour = now.hour.numerator
            minute = now.minute.numerator
            self.display_refresh(0, int(hour / 10))
            self.display_refresh(1, hour % 10, True)
            self.display_refresh(2, int(minute / 10))
            self.display_refresh(3, minute % 10)
        GPIO.output(self.all_channels, GPIO.LOW)
        GPIO.output(self.sequence, GPIO.LOW)

    def display_symbol_num(self, num, symbol, interval):
        decade = int(num / 10)
        single_digit = int(num % 10)
        decimal = int((num - (single_digit + decade * 10)) * 10)
        stat_time = time.time()
        while time.time() - stat_time <= interval:
            self.display_refresh(0, decade)
            self.display_refresh(1, single_digit, True)
            self.display_refresh(2, decimal)
            self.display_refresh(3, symbol)
        GPIO.output(self.all_channels, GPIO.LOW)
        GPIO.output(self.sequence, GPIO.LOW)

    def display_warning(self, interval, cycle):
        for i in range(cycle):
            self.display_str(8888, 0.3)
            time.sleep(interval)
        GPIO.output(self.all_channels, GPIO.LOW)
        GPIO.output(self.sequence, GPIO.LOW)


class BodyInfraredSensor(Device, ABC):

    def __init__(self, device_id, channel):
        super().__init__(device_id)
        self.channel = channel
        GPIO.setup(channel, GPIO.IN)

    def detection(self):
        return GPIO.input(self.channel)


class OledDisplay(Device, ABC):

    def __init__(self, device_id, port=1, address=0x3c, width=128, height=32,
                 font=ImageFont.truetype('./resource/msyhl.ttc', 13)):
        super().__init__(device_id)
        self.fount = font
        self.port = port
        self.address = address
        self.width = width
        self.height = height
        self.serial = i2c(port=port, address=address)
        self.device = ssd1306(self.serial, width=width, height=height)

    def display_info(self, t='无数据', temperature='无数据', humidity='无数据'):
        with canvas(self.device) as draw:
            draw.text((0, 0), ('当前时间:' + t), fill='white', font=self.fount)
            draw.text((0, 13), (str(temperature) + '℃ ' + str(humidity) + '%rh'), fill='white', font=self.fount)


class LoudSpeakerBox(Device, ABC):

    def __init__(self, device_id):
        super().__init__(device_id)
        self.lock = threading.RLock()

    def playFile(self, filename):
        self.lock.acquire()
        wave_obj = audio.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
        self.lock.release()
