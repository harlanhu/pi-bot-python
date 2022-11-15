from devices.buzzer import Buzzer


class DeviceManager:
    """
    设备管理器
    """

    def __init__(self, devices=None):
        if devices is None:
            devices = dict()
        self.devices = devices
        self.setup()

    def setup(self):
        default_buzzer = self.devices.get("default-buzzer")  # type:Buzzer
        default_buzzer.play()

    def get_devices(self):
        return self.devices

    def get_all_devices(self):
        return self.devices.values()

    def get_all_device_id(self):
        return self.devices.keys()

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def logoff_device(self, device_id):
        self.devices.pop(device_id)

    def destroy(self):
        self.devices = None
