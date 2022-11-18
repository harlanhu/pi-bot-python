from enum import IntEnum, unique, Enum


@unique
class GpioBmcEnums(IntEnum):
    SDA_3 = 2
    SCL_5 = 3
    GPIO_7 = 4
    TXD_8 = 14
    RXD_10 = 15
    GPIO_11 = 17
    GPIO_12 = 18
    GPIO_13 = 27
    GPIO_15 = 22
    GPIO_16 = 23
    GPIO_18 = 24
    MOSI_19 = 10
    MISO_21 = 9
    GPIO_22 = 25
    SCLK_23 = 11
    CE_24 = 8
    CE_26 = 7
    SDA_27 = 0
    SCL_28 = 1
    GPIO_29 = 5
    GPIO_31 = 6
    GPIO_32 = 12
    GPIO_33 = 13
    GPIO_35 = 19
    GPIO_36 = 16
    GPIO_37 = 26
    GPIO_38 = 20
    GPIO_40 = 21


@unique
class DevicesIdEnums(Enum):

    DEFAULT_BUZZER = 'default-buzzer'

    DEFAULT_SMOG = 'default-smog'

    DEFAULT_THERMOMETER = 'default-thermometer'

    DEFAULT_NIXIE_TUBE = 'default-nixie-tube'

    DEFAULT_BODY_INFRARED_SENSOR = 'default-body-infrared-sensor'


@unique
class FunctionIdEnums(Enum):

    SMOKE_DETECTION = 'smoke-detection'

    Nixie_DISPLAY = 'nixie-display'

    BODY_DETECTION = 'body-detection'


class Constants(Enum):
    DO_TYPE = 0

    AO_TYPE = 1
