import time
import board
import busio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.modules import Module
from kmk.modules.encoder import EncoderHandler
from kmk.modules.layers import Layers

import adafruit_ssd1306

keyboard = KMKKeyboard()

keyboard.row_pins = (board.D0, board.D1, board.D2)
keyboard.col_pins = (board.D3, board.D9, board.D10)
keyboard.diode_orientation = DiodeOrientation.ROW2COL

keyboard.modules.append(Layers())

# rotary encoder
encoder = EncoderHandler()
encoder.pins = ((board.D6, board.D7, board.D8, False),)
encoder.map = [
    ((KC.VOLU, KC.VOLD),),
    ((KC.VOLU, KC.VOLD),),
]
keyboard.modules.append(encoder)

# keys
normal_keys = [
    KC.BRIU, KC.LGUI, KC.W, KC.MUTE,
    KC.BRID, KC.A, KC.S, KC.D,
    KC.LM(1, KC.LCTL),
    KC.MUTE,
]

ctrl_keys = [
    KC.Z, KC.Y, KC.C, KC.V,
    KC.LGUI(KC.TAB), KC.X, KC.A, KC.S,
    KC.TRNS,
    KC.MUTE,
]

keyboard.keymap = [normal_keys, ctrl_keys]

# text for the oled
normal_names = [
    "Brightness Up", "Windows", "W", "Mute",
    "Brightness Down", "A", "S", "D",
    "Ctrl",
]

ctrl_names = [
    "Ctrl+Z", "Ctrl+Y", "Ctrl+C", "Ctrl+V",
    "Win+Tab", "Ctrl+X", "Ctrl+A", "Ctrl+S",
    "Ctrl",
]


class CtrlFix(Module):
    def __init__(self):
        self.ctrl_down = False
        self.removed = False

    def during_bootup(self, keyboard):
        return

    def before_matrix_scan(self, keyboard):
        return

    def after_matrix_scan(self, keyboard):
        return

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if int_coord == 8:
            self.ctrl_down = is_pressed
            if not is_pressed:
                self.removed = False
        elif int_coord == 4 and self.ctrl_down:
            if is_pressed:
                keyboard.keys_pressed.discard(KC.LCTL)
                self.removed = True
            elif self.removed:
                self.removed = False
                keyboard.keys_pressed.add(KC.LCTL)
        return key

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return


keyboard.modules.append(CtrlFix())

i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)


class Screen(Module):
    def __init__(self):
        self.text = "--"
        self.last_draw = 0.0
        self.changed = True

    def during_bootup(self, keyboard):
        self.draw()

    def before_matrix_scan(self, keyboard):
        return

    def after_matrix_scan(self, keyboard):
        return

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if is_pressed:
            if int_coord == 9:
                self.text = "Mute"
            elif int_coord is not None and int_coord < 9:
                if keyboard.active_layers[0] == 1:
                    self.text = ctrl_names[int_coord]
                else:
                    self.text = normal_names[int_coord]
            else:
                self.text = str(key)
            self.changed = True
        return key

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        now = time.monotonic()
        if self.changed and (now - self.last_draw) > 0.1:
            self.draw()
            self.changed = False
            self.last_draw = now

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return

    def draw(self):
        oled.fill(0)
        oled.text("MACROPAD", 24, 2, 1)
        oled.text(self.text[:16], 0, 18, 1)
        oled.show()


keyboard.modules.append(Screen())

if __name__ == "__main__":
    keyboard.go()