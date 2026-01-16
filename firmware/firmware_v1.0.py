import time
import board
import busio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation

from kmk.extensions import Extension
from kmk.extensions.neopixel import NeoPixel
from kmk.extensions.display import Display, SSD1306, TextEntry
from kmk.extensions.encoder import Encoder


keyboard = KMKKeyboard()

# ───────── MATRIX (2×3) ─────────
keyboard.col_pins = (
    board.GP1,   # column 0
    board.GP2,   # column 1
    board.GP4,   # column 2
)
keyboard.row_pins = (
    board.GP0,   # row 0
    board.GP3,   # row 1
)
keyboard.diode_orientation = DiodeOrientation.COLUMNS

# ───────── KEYMAP ─────────
keyboard.keymap = [
    [
        KC.A, KC.B, KC.C,
        KC.D, KC.E, KC.F,
    ]
]

# ───────── RGB (2x SK6812) ─────────
rgb = NeoPixel(
    pin=board.GP26,
    num_pixels=2,
    brightness=0.3,
    auto_write=True,
)
keyboard.extensions.append(rgb)

# ───────── OLED (SSD1306 I2C, 128×32) + "FPS" counter ─────────
# NOTE: busio.I2C takes (SCL, SDA)
i2c_bus = busio.I2C(board.GP7, board.GP6)
display_driver = SSD1306(i2c=i2c_bus, device_address=0x3C)

fps_entry = TextEntry(text='FPS: 0', x=0, y=0)

display = Display(
    display=display_driver,
    entries=[
        fps_entry,
        TextEntry(text='KMK OK', x=0, y=16),
    ],
    width=128,
    height=32,
    brightness=1,
)

keyboard.extensions.append(display)


class FPSCounter(Extension):
    """
    "FPS" here means how many main-loop HID updates per second the firmware is doing.
    This is a useful health/performance indicator for your macro pad + OLED refresh.
    """

    def __init__(self, entry: TextEntry, update_period_s: float = 1.0):
        self.entry = entry
        self.update_period_s = float(update_period_s)
        self._last_t = time.monotonic()
        self._frames = 0

    def on_runtime_enable(self, keyboard):
        pass

    def on_runtime_disable(self, keyboard):
        pass

    def during_bootup(self, keyboard):
        # Reset counters at boot
        self._last_t = time.monotonic()
        self._frames = 0

    def before_matrix_scan(self, keyboard):
        return None

    def after_matrix_scan(self, keyboard):
        return None

    def before_hid_send(self, keyboard):
        return None

    def after_hid_send(self, keyboard):
        # Called very frequently; treat each call as one "frame".
        self._frames += 1
        now = time.monotonic()
        dt = now - self._last_t
        if dt >= self.update_period_s:
            fps = self._frames / dt if dt > 0 else 0
            self.entry.text = f'FPS: {fps:0.0f}'
            self._frames = 0
            self._last_t = now

    def on_powersave_enable(self, keyboard):
        return None

    def on_powersave_disable(self, keyboard):
        return None


keyboard.extensions.append(FPSCounter(fps_entry))

# ───────── ROTARY ENCODER ─────────
encoder = Encoder(
    pins=((board.GP27, board.GP28),),   # A, B
    map=((KC.VOLD, KC.VOLU),),          # CCW, CW
)
keyboard.extensions.append(encoder)

# ───────── STARTUP LED COLOR ─────────
rgb.fill((0, 80, 255))

# ───────── START ─────────
if __name__ == '__main__':
    keyboard.go()
