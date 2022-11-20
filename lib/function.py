import datetime
import threading
import time
from core.devices import NixieTube, Buzzer, Smog, Thermometer, BodyInfraredSensor, OledDisplay


class Function(threading.Thread):

    def __init__(self, thread_id, keep_running=True):
        super().__init__()
        self.thread_id = thread_id
        self.keep_running = keep_running

    def off(self):
        self.keep_running = False


class SmokeDetectionFunction(Function):

    def __init__(self, thread_id, buzzer: Buzzer, smog: Smog, keep_running=True):
        super().__init__(thread_id, keep_running)
        self.buzzer = buzzer
        self.smog = smog
        self.lock = threading.RLock()

    def run(self):
        while self.keep_running:
            has_smoke = self.smog.has_smoke()
            if has_smoke:
                self.lock.acquire()
                self.buzzer.cycle()
                time.sleep(3)
                self.lock.release()


class NixieDisplayFunction(Function):

    def __init__(self, thread_id, nixie_tube: NixieTube, thermometer: Thermometer, keep_running=True):
        super().__init__(thread_id, keep_running)
        self.nixie_tube = nixie_tube
        self.thermometer = thermometer
        self.lock = threading.RLock()

    def run(self):
        while True:
            self.nixie_tube.display_time(10)
            result = self.thermometer.detection()
            if result:
                humidity, temperature = result
                self.nixie_tube.display_content(str(temperature) + '^', 10)
                self.nixie_tube.display_content(str(humidity) + '%', 10)
            else:
                print("Thermometer data are wrong,skip")
            self.nixie_tube.display_content('Do not touch')


class BodyDetectionFunction(Function):

    def __init__(self, thread_id, body_infrared_sensor: BodyInfraredSensor, buzzer: Buzzer):
        super().__init__(thread_id)
        self.body_infrared_sensor = body_infrared_sensor
        self.buzzer = buzzer
        self.lock = threading.RLock()

    def run(self):
        count = 0
        while True:
            if self.body_infrared_sensor.detection():
                print('========警告=======')
                print('！！！！请勿触碰！！！！\n！！！！有电危险！！！！\n' * 3)
                print('警告次数:', count)
                self.buzzer.cycle(0.2, 3, 0.5, 10)
                count += 1
            time.sleep(1)


class OledDisplayFunction(Function):

    def __init__(self, thread_id, oled_display: OledDisplay, thermometer: Thermometer):
        super().__init__(thread_id)
        self.oled_display = oled_display
        self.thermometer = thermometer

    def run(self):
        while True:
            t = datetime.datetime.now().strftime('%H:%M:%S')
            humidity, temperature = self.thermometer.detection()
            self.oled_display.display_info(t, temperature, humidity)

