import threading
import time


class Function(threading.Thread):

    def __init__(self, thread_id, keep_running=True):
        super().__init__()
        self.thread_id = thread_id
        self.keep_running = keep_running

    def off(self):
        self.keep_running = False


class SmokeDetectionFunction(Function):

    def __init__(self, thread_id, buzzer, smog, keep_running):
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
