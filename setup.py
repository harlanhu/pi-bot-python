import time

import gpio.gpio as gpio
from devices.constants import Constants
from devices.buzzer import Buzzer
from devices.device_manager import DeviceManager
from devices.smog import Smog
from enums.gpio_enums import GpioBmcEnums


def setup_devices():
    buzzer = Buzzer('default-buzzer', GpioBmcEnums.GPIO_7)
    smog = Smog('default-smog', GpioBmcEnums.GPIO_11, Constants.DO_TYPE)
    return {
        buzzer.device_id: buzzer,
        smog.device_id: smog
    }


device_manager = None

if __name__ == '__main__':
    try:
        devices = setup_devices()
        device_manager = DeviceManager(devices)
        while True:
            smog = devices.get('default-smog')  # type:Smog
            buzzer = devices.get('default-buzzer')  # type:Buzzer
            if not smog.has_smog():
                buzzer.play_cycle(0.2, 3, 0.5, 3)
                time.sleep(5)
    except KeyboardInterrupt:
        gpio.destroy()
        if device_manager is not None:
            device_manager.destroy()
