from core.devices import Buzzer, Smog, Thermometer, Constants, DeviceManager, NixieTube
from lib.enums import DevicesIdEnums, GpioBmcEnums, FunctionIdEnums
from lib.function import Function, SmokeDetectionFunction, NixieDisplayFunction
from core.gpio import GPIO


class FunctionManager:

    def __init__(self):
        print("RPI INFO:" + str(GPIO.RPI_INFO))
        self.buzzer = Buzzer(DevicesIdEnums.DEFAULT_BUZZER, GpioBmcEnums.GPIO_7)
        self.smog = Smog(DevicesIdEnums.DEFAULT_SMOG, GpioBmcEnums.GPIO_11, Constants.DO_TYPE)
        self.thermometer = Thermometer(DevicesIdEnums.DEFAULT_THERMOMETER, GpioBmcEnums.GPIO_12)
        self.nixie_tube = NixieTube(DevicesIdEnums.DEFAULT_NIXIE_TUBE, GpioBmcEnums.GPIO_13, GpioBmcEnums.GPIO_15,
                                    GpioBmcEnums.GPIO_16, GpioBmcEnums.GPIO_18, GpioBmcEnums.GPIO_22,
                                    GpioBmcEnums.GPIO_29, GpioBmcEnums.GPIO_31, GpioBmcEnums.GPIO_32,
                                    GpioBmcEnums.GPIO_33, GpioBmcEnums.GPIO_35, GpioBmcEnums.GPIO_36,
                                    GpioBmcEnums.GPIO_37)
        self.function_threads_dict = {}
        devices_dict = {
            self.buzzer.device_id: self.buzzer,
            self.smog.device_id: self.smog,
            self.thermometer.device_id: self.thermometer,
            self.nixie_tube.device_id: self.nixie_tube
        }
        self.device_manager = DeviceManager(devices_dict)

    # 烟雾探测
    def smoke_detection(self):
        smoke_detection_function = SmokeDetectionFunction(FunctionIdEnums.SMOKE_DETECTION, self.buzzer, self.smog)
        self.function_threads_dict.update({
            smoke_detection_function.thread_id: smoke_detection_function,
        })
        smoke_detection_function.start()

    def display_roll(self):
        time_display = NixieDisplayFunction(FunctionIdEnums.Nixie_DISPLAY, self.nixie_tube, self.thermometer)
        self.function_threads_dict.update({
            time_display.thread_id: time_display
        })
        time_display.start()

    def stop_function(self, function_id):
        function = self.function_threads_dict.get(function_id)  # type:Function
        function.off()

    def off(self):
        for function in self.function_threads_dict.values():
            function.off()
            self.function_threads_dict.pop(function)
        self.device_manager.devices = {}
