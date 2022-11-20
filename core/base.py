from core.devices import Buzzer, Smog, Thermometer, Constants, DeviceManager, NixieTube, BodyInfraredSensor, OledDisplay
from lib.enums import DevicesIdEnums, GpioBmcEnums, FunctionIdEnums
from lib.function import Function, SmokeDetectionFunction, NixieDisplayFunction, BodyDetectionFunction, \
    OledDisplayFunction
from core.gpio import GPIO


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

    def stop_function(self, function_id):
        function = self.function_threads_dict.get(function_id)  # type:Function
        function.off()

    def off(self):
        for function in self.function_threads_dict.values():
            function.off()
            self.function_threads_dict.pop(function)
        self.device_manager.devices = {}
