import datetime
import threading
import time
import smbus as smbus
import cv2 as cv
import Adafruit_DHT
import simpleaudio as audio
from abc import abstractmethod, ABC
from pathlib import Path
from PIL import ImageFont, Image
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.core.sprite_system import framerate_regulator
from luma.oled.device import ssd1306
from lib.enums import Constants, DevicesId
from core.gpio import GPIO
from lib.utils import TimeUtils, WeatherUtils


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
        for device in devices_dict.values():
            device_enum = device.device_id  # type: DevicesId
            print('正在启动 ', device_enum.value)
            threading.Thread(target=device.setup()).start()

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
        self.lock.acquire()
        GPIO.output(self.channel, GPIO.HIGH)
        self.lock.release()

    def play(self, duration=0.2):
        GPIO.output(self.channel, GPIO.LOW)
        time.sleep(duration)
        GPIO.output(self.channel, GPIO.HIGH)

    def loop(self, duration=0.2, loop=1):
        for i in range(loop):
            self.play(duration)

    def cycle(self, duration=0.2, loop=3, interval=0.5, cycle=1):
        for i in range(cycle):
            self.loop(duration, loop)
            time.sleep(interval)


class Smog(Device, ABC):

    def __init__(self, device_id, channel, mode, adc=None, threshold=0):
        super().__init__(device_id)
        self.channel = channel
        self.mode = mode
        self.adc = adc
        self.threshold = threshold
        if mode == Constants.DO_TYPE:
            GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def has_smoke(self):
        self.lock.acquire()
        if self.mode == Constants.DO_TYPE:
            val = not GPIO.input(self.channel)
        else:
            val = self.adc.read(self.channel) >= self.threshold
        self.lock.release()
        return val

    def get_concentration(self):
        self.lock.acquire()
        if self.mode == Constants.DO_TYPE:
            val = '当前DO模式无法读取数值'
        else:
            val = self.adc.read(self.channel)
        self.lock.release()
        return val


class Thermometer(Device, ABC):

    def __init__(self, device_id, channel):
        super().__init__(device_id)
        self.channel = channel
        self.humidity = 0
        self.temperature = 0
        time.sleep(1)
        self.detection()

    def detection(self):
        self.lock.acquire()
        self.humidity, self.temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, self.channel)
        self.lock.release()
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

    def __init__(self, device_id, port=1, address=0x3c, width=128, height=32, fps=30,
                 font=ImageFont.truetype('./resource/msyhl.ttc', 12)):
        super().__init__(device_id)
        # 1796236
        self.fount = font
        self.port = port
        self.address = address
        self.width = width
        self.height = height
        self.serial = i2c(port=port, address=address)
        self.regulator = framerate_regulator(fps=fps)
        self.device = ssd1306(self.serial, width=width, height=height)

    def setup(self):
        img_path = str(Path(__file__).parent.resolve().parent.joinpath('resource', 'pi_logo.png'))
        logo = Image.open(img_path).convert('RGBA')
        fff = Image.new('RGBA', logo.size, (255,) * 4)
        background = Image.new("RGBA", self.device.size, "white")
        posn = ((self.device.width - logo.width) // 2, 0)
        start_time = time.time()
        while time.time() - start_time <= 5:
            for angle in range(0, 360, 2):
                rot = logo.rotate(angle, resample=Image.BILINEAR)
                img = Image.composite(rot, fff, rot)
                background.paste(img, posn)
                self.device.display(background.convert(self.device.mode))

    def display_time(self, t: datetime.datetime):
        date = t.strftime('%Y年%m月%d日')
        times = t.strftime('%H:%M:%S')
        week = t.strftime('%w')
        with canvas(self.device) as draw:
            draw.text((2, 0), date + ' ' + TimeUtils.weeks[int(week)], fill='white', font=self.fount)
            draw.text((40, 15), times, fill='white', font=self.fount)

    def display_weather(self):
        font = ImageFont.truetype('./resource/fontawesome-webfont.ttf', self.device.height - 10)
        with canvas(self.device) as draw:
            if WeatherUtils.has_data:
                draw.text((2, 0), WeatherUtils.province + ',' + WeatherUtils.city + ':'
                          + WeatherUtils.temperature + '℃,'
                          + WeatherUtils.weather,
                          fill='white', font=self.fount)
                draw.text((2, 15), '湿度:' + WeatherUtils.humidity + '%,'
                          + WeatherUtils.wind_direction + '风,'
                          + WeatherUtils.wind_power + '级',
                          fill='white', font=self.fount)
            else:
                w, h = draw.textsize(text='\uf05a', font=font)
                left = (self.device.width - w) / 2
                top = (self.device.height - h) / 2
                draw.text((left, top), text='\uf05a', font=font, fill="white")

    def display_temperature(self, temperature, humidity):
        with canvas(self.device) as draw:
            draw.text((2, 0), ('室内温度: ' + str(temperature) + ' ℃'), fill='white', font=self.fount)
            draw.text((2, 15), ('室内湿度: ' + str(humidity) + ' %RH'), fill='white', font=self.fount)


class LoudSpeakerBox(Device, ABC):

    def __init__(self, device_id):
        super().__init__(device_id)
        self.lock = threading.RLock()

    def play_file(self, filename):
        self.lock.acquire()
        wave_obj = audio.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()
        self.lock.release()


class PCF8591(Device, ABC):

    def __init__(self, device_id, bus=1, addr=0x48):
        super().__init__(device_id)
        self.addr = addr
        self.smbus = smbus.SMBus(bus)

    def read(self, channel):
        val = 0x40
        if channel == 0:
            val = 0x40
        if channel == 1:
            val = 0x41
        if channel == 2:
            val = 0x42
        if channel == 3:
            val = 0x43
        self.smbus.write_byte(self.addr, val)
        return self.smbus.read_byte(self.addr)

    def write(self, val):
        # 将字符串值移动到temp
        temp = val
        # 将字符串改为整数类型
        temp = int(temp)
        # 写入字节数据，将数字值转化成模拟值从 AOUT 输出
        self.smbus.write_byte_data(self.addr, 0x40, temp)


class Camera(Device, ABC):

    # 高电平为常规模式，低电平为红外模式
    def __init__(self, device_id, channel, width=640, height=480, framerate=60, file_path='./file/camera'):
        super().__init__(device_id)
        self.channel = channel
        self.cap = cv.VideoCapture(0)
        self.cap.set(cv.CAP_PROP_FPS, framerate)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        self.face_detect = cv.CascadeClassifier('/usr/local/app/project/pi-bot/resource/face-data/haarcascades/haarcascade_frontalface_default.xml')
        self.file_path = file_path
        self.infrared_mode = 1
        GPIO.setup(channel, GPIO.OUT)
        GPIO.output(channel, GPIO.HIGH)

    def is_infrared_on(self):
        return self.infrared_mode == 0

    def turn_on_infrared(self):
        if self.infrared_mode == 1:
            self.infrared_mode = 0
            GPIO.output(self.channel, GPIO.LOW)
            print('摄像头红外模式:on')

    def turn_off_infrared(self):
        if self.infrared_mode == 0:
            self.infrared_mode = 1
            GPIO.output(self.channel, GPIO.HIGH)
            print('摄像头红外模式:off')

    def capture(self):
        ret, frame = self.cap.read()
        frame = cv.flip(frame, 1)
        if ret:
            self.face_detection(frame)
        cv.imshow("frame", frame)
        if cv.waitKey(1) == ord('q'):
            self.off()
        time.sleep(self.cap.get(cv.CAP_PROP_FPS) / 1000)
        return frame

    def off(self):
        self.cap.release()

    def face_detection(self, frame):
        faces = self.face_detect.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=3, minSize=(32, 32))
        for x, y, w, h in faces:
            cv.rectangle(frame, pt1=(x, y), pt2=(x + w, y + h), color=[0, 0, 255], thickness=2)
            cv.circle(frame, center=(x + w // 2, y + h // 2), radius=w // 2, color=[0, 255, 0], thickness=2)
        return frame
