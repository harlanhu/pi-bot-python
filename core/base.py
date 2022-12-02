from core import schedule_task
from core.devices import DeviceManager
from core.function import FunctionManager, SmokeDetectionFunction, BodyDetectionFunction, ThermometerFunction, \
    OledDisplayFunction, LightingDetectionFunction, VideoOutputFunction
from core.gpio import GPIO
from lib.enums import DevicesId, FunctionId


class Bot:

    def __init__(self, config, device_manager: DeviceManager, function_manager: FunctionManager):
        print('Hello World! This is Pi Bot!')
        print("RPI INFO:" + str(GPIO.RPI_INFO))
        self.device_manager = device_manager
        self.function_manager = function_manager

    def on(self):
        self.smoke_detection()
        self.body_detection()
        self.thermometer_detection()
        self.oled_display_info()
        self.lighting_detection()
        self.video_output()

    def destroy(self):
        self.function_manager.stop_all()
        self.device_manager.destroy()

    def smoke_detection(self):
        smoke_detection_function = SmokeDetectionFunction(FunctionId.SMOKE_DETECTION,
                                                          self.device_manager.get_device(DevicesId.DEFAULT_BUZZER),
                                                          self.device_manager.get_device(DevicesId.DEFAULT_SMOG))
        self.function_manager.register(smoke_detection_function.thread_id, smoke_detection_function)

    def body_detection(self):
        body_detection_function = BodyDetectionFunction(FunctionId.BODY_DETECTION,
                                                        self.device_manager.get_device(DevicesId.DEFAULT_BODY_INFRARED_SENSOR),
                                                        self.device_manager.get_device(DevicesId.DEFAULT_BUZZER))
        self.function_manager.register(body_detection_function.thread_id, body_detection_function)

    def thermometer_detection(self):
        thermometer_detection = ThermometerFunction(FunctionId.THERMOMETER_DETECTION,
                                                    self.device_manager.get_device(DevicesId.DEFAULT_THERMOMETER))
        self.function_manager.register(thermometer_detection.thread_id, thermometer_detection)

    def oled_display_info(self):
        schedule_task.weather_task()
        oled_display_function = OledDisplayFunction(FunctionId.OLED_DISPLAY,
                                                    self.device_manager.get_device(DevicesId.DEFAULT_OLED_DISPLAY),
                                                    self.device_manager.get_device(DevicesId.DEFAULT_THERMOMETER))
        self.function_manager.register(oled_display_function.thread_id, oled_display_function)

    def lighting_detection(self):
        lighting_detection_function = LightingDetectionFunction(FunctionId.LIGHTING_DETECTION,
                                                                self.device_manager.get_device(DevicesId.DEFAULT_PCF8591),
                                                                0,
                                                                self.device_manager.get_device(DevicesId.DEFAULT_CAMERA))
        self.function_manager.register(lighting_detection_function.thread_id, lighting_detection_function)

    def video_output(self):
        video_output_function = VideoOutputFunction(FunctionId.VIDEO_OUTPUT,
                                                    self.device_manager.get_device(DevicesId.DEFAULT_CAMERA))
        self.function_manager.register(video_output_function.thread_id, video_output_function)



