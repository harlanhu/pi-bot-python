from devices.constants import Constants
from gpio.gpio import GPIO


class Smog:

    def __init__(self, device_id, do_pin, mode):
        self.device_id = device_id
        self.do_pin = do_pin
        self.mode = mode
        if mode == Constants.DO_TYPE:
            GPIO.setup(do_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def has_smog(self):
        if self.mode == Constants.DO_TYPE:
            return GPIO.input(self.do_pin)
