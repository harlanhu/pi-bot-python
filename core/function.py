import datetime
import threading
import time
from abc import abstractmethod, ABC
from core.devices import NixieTube, Buzzer, Smog, Thermometer, BodyInfraredSensor, OledDisplay


class FunctionManager:

    def __init__(self):
        self.function_threads_dict = {}

    def register(self, function_id, function):
        self.function_threads_dict.update({function_id: function})
        function.start()

    def pause_function(self, function_id):
        function = self.function_threads_dict.get(function_id)  # type:Function
        function.pause()

    def pause_all(self):
        for function in self.function_threads_dict.values():
            function.pause()

    def resume_function(self, function_id):
        function = self.function_threads_dict.get(function_id)  # type:Function
        function.resume()

    def resume_all(self):
        for function in self.function_threads_dict.values():
            function.resume()

    def stop_function(self, function_id):
        function = self.function_threads_dict.get(function_id)  # type:Function
        function.stop()

    def stop_all(self):
        for function in self.function_threads_dict.values():
            function.stop()
            self.function_threads_dict.pop(function)


class Function(threading.Thread):

    def __init__(self, thread_id):
        super().__init__()
        self.thread_id = thread_id
        self.status = threading.Event()
        self.status.set()
        self.running = threading.Event()
        self.running.set()
        self.lock = threading.RLock()

    def pause(self):
        self.lock.acquire()
        self.status.clear()
        self.lock.release()

    def resume(self):
        self.lock.acquire()
        self.status.set()
        self.lock.release()

    def stop(self):
        self.lock.acquire()
        self.status.set()
        self.running.clear()
        self.lock.release()

    def run(self):
        while self.running.isSet():
            self.status.wait()
            self.function()

    @abstractmethod
    def function(self):
        pass


class SmokeDetectionFunction(Function, ABC):

    def __init__(self, thread_id, buzzer: Buzzer, smog: Smog):
        super().__init__(thread_id)
        self.buzzer = buzzer
        self.smog = smog

    def function(self):
        has_smoke = self.smog.has_smoke()
        if has_smoke:
            self.buzzer.cycle()
            time.sleep(3)


class NixieDisplayFunction(Function, ABC):

    def __init__(self, thread_id, nixie_tube: NixieTube, thermometer: Thermometer):
        super().__init__(thread_id)
        self.nixie_tube = nixie_tube
        self.thermometer = thermometer

    def function(self):
        self.nixie_tube.display_time(10)
        result = self.thermometer.detection()
        if result:
            humidity, temperature = result
            self.nixie_tube.display_content(str(temperature) + '^', 10)
            self.nixie_tube.display_content(str(humidity) + '%', 10)
        else:
            print("Thermometer data are wrong,skip")
        self.nixie_tube.display_content('Do not touch')


class BodyDetectionFunction(Function, ABC):

    def __init__(self, thread_id, body_infrared_sensor: BodyInfraredSensor, buzzer: Buzzer):
        super().__init__(thread_id)
        self.body_infrared_sensor = body_infrared_sensor
        self.buzzer = buzzer
        self.warning_time = 0

    def function(self):
        if self.body_infrared_sensor.detection():
            print('========警告=======')
            print('！！！！请勿触碰！！！！\n！！！！有电危险！！！！\n' * 3)
            print('警告次数:', self.warning_time)
            self.buzzer.cycle(0.2, 3, 0.5, 10)
            self.warning_time += 1
        time.sleep(1)


class ThermometerFunction(Function, ABC):

    def __init__(self, thread_id, thermometer: Thermometer):
        super().__init__(thread_id)
        self.thermometer = thermometer

    def function(self):
        self.thermometer.detection()
        time.sleep(5)


class OledDisplayFunction(Function, ABC):

    def __init__(self, thread_id, oled_display: OledDisplay, thermometer: Thermometer):
        super().__init__(thread_id)
        self.oled_display = oled_display
        self.thermometer = thermometer
        self.date_time = 'unknown'

    def function(self):
        t = datetime.datetime.now()
        if self.date_time == t:
            return
        self.oled_display.display_info(t.strftime('%H:%M:%S'), self.thermometer.temperature, self.thermometer.humidity)
