import time

from lib.function import Function


class SmokeDetectionFunction(Function):

    def __init__(self, thread_id, buzzer, smog):
        super().__init__()
        self.thread_id = thread_id
        self.buzzer = buzzer
        self.smog = smog
        self.keep_running = True

    def run(self):
        while self.keep_running:
            has_smoke = self.smog.has_smoke()
            if has_smoke:
                self.buzzer.cycle()
                time.sleep(3)

    def stop(self):
        self.keep_running = False
