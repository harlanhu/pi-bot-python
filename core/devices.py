import datetime
import time
import numpy as np
from lib.enums import DevicesIdEnums, Constants
from core.gpio import GPIO
import Adafruit_DHT


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
        self.hsa_setup = False

    def detection_test(self):
        print("========DHT11 Detection========")
        GPIO.setup(self.channel, GPIO.OUT)
        GPIO.output(self.channel, GPIO.LOW)
        # 给信号提示传感器开始工作,并保持低电平18ms以上
        time.sleep(0.02)
        # 输出高电平
        GPIO.output(self.channel, GPIO.HIGH)
        # 发送完开始信号后把输出模式换成输入模式，不然信号线上电平始终被拉高
        GPIO.setup(self.channel, GPIO.IN)
        print("completion of signal transmission...")
        # DHT11发出应答信号，输出 80 微秒的低电平
        while GPIO.input(self.channel) == GPIO.LOW:
            print('wait for DHT11 response...')
            continue
        # 紧接着输出 80 微秒的高电平通知外设准备接收数据
        while GPIO.input(self.channel) == GPIO.HIGH:
            print('wait for DHT11 transmit data...')
            continue
        print('raspberry pi receiving data...')
        # 开始接收数据
        count = 0  # 计数器
        data = []  # 收到的二进制数据
        while count < 40:
            # 先是 50 微秒的低电平
            while GPIO.input(self.channel) == GPIO.LOW:
                continue
            start_time = time.time()
            # 接着是26-28微秒的高电平，或者 70 微秒的高电平
            while GPIO.input(self.channel) != GPIO.HIGH:
                continue
            spend_time = time.time() - start_time
            if 0.000025 < spend_time < 0.000029:
                # 26-28 微秒时高电平
                data.append(0)
            else:
                # 70 微秒时高电平
                data.append(1)
            count += 1
        print('completion of reception, processing data...')
        # logspace()函数用于创建一个于等比数列的数组
        series = np.logspace(7, 0, 8, base=2, dtype=int)
        # 将data列表转换为数组
        data_array = np.array(data)
        # dot()函数对于两个一维的数组，计算的是这两个数组对应下标元素的乘积和(数学上称之为内积)
        humidity = series.dot(data_array[0:8])  # 用前8位二进制数据计算湿度的十进制值
        humidity_point = series.dot(data_array[8:16])
        temperature = series.dot(data_array[16:24])
        temperature_point = series.dot(data_array[24:32])
        check = series.dot(data_array[32:40])
        tmp = humidity + humidity_point + temperature + temperature_point
        print('return to the result')
        # 十进制的数据相加
        if check == tmp:  # 数据校验，相等则输出
            return humidity, temperature
        else:  # 错误输出错误信息
            return False

    def detection(self):
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, self.channel)
        return humidity, temperature


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

    def on(self):
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


class BodyInfraredSensor(Device):

    def __init__(self, device_id, channel):
        super().__init__(device_id)
        self.channel = channel
        GPIO.setup(channel, GPIO.IN)

    def detection(self):
        return GPIO.input(self.channel)
