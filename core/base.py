from core.devices import Buzzer, Smog, Thermometer, Constants, DeviceManager
from lib.enums import DevicesIdEnums, GpioBmcEnums
from lib.function import Function
from lib.function_thread import SmokeDetectionFunction
from core.gpio import GPIO


class Bot:

    def __init__(self):
        print("RPI INFO:" + str(GPIO.RPI_INFO))
        self.buzzer = Buzzer(DevicesIdEnums.DEFAULT_BUZZER, GpioBmcEnums.GPIO_7)
        self.smog = Smog(DevicesIdEnums.DEFAULT_SMOG, GpioBmcEnums.GPIO_11, Constants.DO_TYPE)
        self.thermometer = Thermometer(DevicesIdEnums.DEFAULT_THERMOMETER, GpioBmcEnums.GPIO_12)
        self.function_threads_dict = {}
        devices_dict = {
            self.buzzer.device_id: self.buzzer,
            self.smog.device_id: self.smog,
            self.thermometer.device_id: self.thermometer
        }
        self.device_manager = DeviceManager(devices_dict)

    # 烟雾探测
    def smoke_detection(self):
        self.buzzer.loop()
        smoke_detection_function = SmokeDetectionFunction('smoke_detection', self.buzzer, self.smog)
        self.function_threads_dict.update({smoke_detection_function.thread_id: smoke_detection_function})
        smoke_detection_function.start()

    def stop_function(self, function_id):
        function = self.function_threads_dict.get(function_id)  # type:Function
        function.stop()

    def off(self):
        for function in self.function_threads_dict:
            function.stop()
            self.function_threads_dict.pop(function)
        self.device_manager.devices = {}
