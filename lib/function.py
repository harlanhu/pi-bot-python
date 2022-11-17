import threading
import time
from core.devices import NixieTube, Buzzer, Smog, Thermometer


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
                self.nixie_tube.display_symbol_num(temperature, '^', 10)
                self.nixie_tube.display_symbol_num(humidity, '%', 10)
            else:
                print("Thermometer data are wrong,skip")
            self.nixie_tube.display_content('Happy Birthday')



