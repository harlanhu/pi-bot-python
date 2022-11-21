import datetime
import threading
import time
from abc import abstractmethod, ABC
from core.gpio import GPIO
from core.devices import NixieTube, Buzzer, Smog, Thermometer, BodyInfraredSensor, OledDisplay, DeviceManager
from lib.enums import DevicesIdEnums, GpioBmcEnums, FunctionIdEnums, Constants


class FunctionManager:

    def __init__(self):
        print("RPI INFO:" + str(GPIO.RPI_INFO))
        self.buzzer = Buzzer(DevicesIdEnums.DEFAULT_BUZZER, GpioBmcEnums.GPIO_7)
        self.smog = Smog(DevicesIdEnums.DEFAULT_SMOG, GpioBmcEnums.GPIO_11, Constants.DO_TYPE)
        self.thermometer = Thermometer(DevicesIdEnums.DEFAULT_THERMOMETER, GpioBmcEnums.GPIO_12)
        self.body_infrared_sensor = BodyInfraredSensor(DevicesIdEnums.DEFAULT_BODY_INFRARED_SENSOR,
                                                       GpioBmcEnums.GPIO_13)
        self.oled_display = OledDisplay(DevicesIdEnums.DEFAULT_OLED_DISPLAY)
        self.function_threads_dict = {}
        devices_dict = {
            self.buzzer.device_id: self.buzzer,
            self.smog.device_id: self.smog,
            self.thermometer.device_id: self.thermometer,
            self.body_infrared_sensor.device_id: self.body_infrared_sensor,
            self.oled_display.device_id: self.oled_display
        }
        self.device_manager = DeviceManager(devices_dict)

    # 烟雾探测
    def smoke_detection(self):
        smoke_detection_function = SmokeDetectionFunction(FunctionIdEnums.SMOKE_DETECTION, self.buzzer, self.smog)
        self.function_threads_dict.update({
            smoke_detection_function.thread_id: smoke_detection_function,
        })
        smoke_detection_function.start()

    def body_detection(self):
        body_detection_function = BodyDetectionFunction(FunctionIdEnums.BODY_DETECTION, self.body_infrared_sensor,
                                                        self.buzzer)
        self.function_threads_dict.update({
            body_detection_function.thread_id: body_detection_function
        })
        body_detection_function.start()

    def oled_display_info(self):
        oled_display_function = OledDisplayFunction(FunctionIdEnums.OLED_DISPLAY, self.oled_display, self.thermometer)
        self.function_threads_dict.update({
            oled_display_function.thread_id: oled_display_function
        })
        oled_display_function.start()

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
        self.device_manager.devices = {}


class Function(threading.Thread):

    def __init__(self, thread_id):
        super().__init__()
        self.thread_id = thread_id
        self.status = threading.Event()
        self.running = threading.Event()
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
        self.lock = threading.RLock()

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


class OledDisplayFunction(Function, ABC):

    def __init__(self, thread_id, oled_display: OledDisplay, thermometer: Thermometer):
        super().__init__(thread_id)
        self.oled_display = oled_display
        self.thermometer = thermometer

    def function(self):
        while True:
            t = datetime.datetime.now().strftime('%H:%M:%S')
            humidity, temperature = self.thermometer.detection()
            self.oled_display.display_info(t, temperature, humidity)
