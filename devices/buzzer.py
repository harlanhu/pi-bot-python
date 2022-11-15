import time
from gpio.gpio import GPIO


# 有源蜂鸣器: 高电平无声/低电平发声
class Buzzer:
    """
    蜂鸣器
    """
    def __init__(self, device_id, ctr_pin):
        self.device_id = device_id
        self.ctr_pin = ctr_pin
        GPIO.setup(self.ctr_pin, GPIO.OUT, initial=GPIO.HIGH)

    def play(self, duration=0.2):
        GPIO.output(self.ctr_pin, GPIO.LOW)
        time.sleep(duration)
        GPIO.output(self.ctr_pin, GPIO.HIGH)

    def play_loop(self, duration=0.2, loop=1):
        for i in range(loop):
            self.play(duration)

    def play_cycle(self, duration=0.2, loop=3, interval=0.5, cycle=1):
        for i in range(cycle):
            self.play_loop(duration, loop)
            time.sleep(interval)

    def play_stop(self):
        GPIO.setup(self.ctr_pin, GPIO.HIGH)
