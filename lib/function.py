import threading


class Function(threading.Thread):

    def __init__(self, keep_running=True):
        super().__init__()
        self.keep_running = keep_running

    def stop(self):
        self.keep_running = False
