import atexit
import collections
import enum
import struct

import hid

VENDOR_IDS = [1118]
PRODUCT_IDS = [654]


Packet = collections.namedtuple('Packet', [
    'command',  # Byte
    'size',  # Byte
])


HAT = collections.namedtuple('HAT', [
    'x',  # Signed short
    'y',  # Signed short
])


Report = collections.namedtuple('Report', [
    'header',   # 2 bytes
    'buttons',  # 2 bytes
    'trigL',    # 1 byte
    'trigR',    # 1 byte
    'HATL',     # 4 bytes
    'HATR',     # 4 bytes
])


class Button(enum.Enum):
    HatRight      = 0x8000
    HatLeft       = 0x4000
    Back          = 0x2000
    Start         = 0x1000
    DigiRight     = 0x0800
    DigiLeft      = 0x0400
    DigiDown      = 0x0200
    DigiUp        = 0x0100
    Y             = 0x0080
    X             = 0x0040
    B             = 0x0020
    A             = 0x0010
    Reserved      = 0x0008
    XBox          = 0x0004
    ShoulderRight = 0x0002
    ShoulderLeft  = 0x0001


class LedPattern(enum.Enum):
    Off          = 0x00
    BlinkingAll  = 0x01
    FlashOn1     = 0x02
    FlashOn2     = 0x03
    FlashOn3     = 0x04
    FlashOn4     = 0x05
    On1          = 0x06
    On2      =     0x07
    On3          = 0x07
    On4          = 0x08
    Rotating     = 0x0a
    Blinking     = 0x0b
    BlinkingSlow = 0x0c
    Alternating  = 0x0d


class Controller:

    def __init__(self, product_id, vendor_id, serial_number):
        self.product_id = product_id
        self.vendor_id = vendor_id
        self.serial_number = serial_number
        self.device = hid.device()
        self._opened = False
        self._product_string = None

    @property
    def product_string(self):
        if self._product_string is None:
            opened = not self._opened
            self.open()
            self._product_string = self.device.get_product_string()
            if opened:
                self.close()
        return self._product_string

    def open(self):
        if not self._opened:
            self.device.open(self.vendor_id, self.product_id, self.serial_number)
            self._opened = True

    def close(self):
        if self._opened:
            self._opened = False
            self.device.close()

    def set_led_pattern(self, pattern):
        if not isinstance(pattern, LedPattern):
            pattern = LedPattern(pattern)
        self._write([1, 3, pattern.value])

    def read_report(self, timeout=25):
        buf = self.device.read(20, timeout)

        if buf:
            mask = struct.unpack('>H', bytes(buf[2:4]))[0]
            buttons = tuple(button for button in Button if mask & button.value)

            return Report(
                Packet(*buf[:2]),                               # header
                buttons,                                        # buttons
                buf[4], buf[5],                                 # Trigger L/R
                HAT(*struct.unpack('<hh', bytes(buf[6:10]))),   # HAT Left
                HAT(*struct.unpack('<hh', bytes(buf[10:14]))),  # HAT Right
            )

    def _write(self, bytes):
        self.open()
        self.device.write(bytes)

    def __str__(self):
        return self.product_string

    def __repr__(self):
        return '<Xbox360 Controller %s>' % self.serial_number


def enumerate_controllers():
    """ Returns a list of controllers. """
    controllers = []
    for device in hid.enumerate():
        if device.get('vendor_id') in VENDOR_IDS and \
               device['product_id'] in PRODUCT_IDS:
            controllers.append(Controller(device['product_id'], device['vendor_id'], device['serial_number']))

    return controllers

