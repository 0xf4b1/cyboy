#  SPDX-License-Identifier: GPL-3.0-only

import threading

from pynput.keyboard import Key, Listener, KeyCode

from controls.controls import *

mapping = {
    Key.down: DOWN,
    Key.up: UP,
    Key.left: LEFT,
    Key.right: RIGHT,
    Key.enter: START,
    Key.backspace: SELECT,
    KeyCode.from_char('s'): B,
    KeyCode.from_char('a'): A
}


class KeyboardControls(Controls):

    def __init__(self):
        control = threading.Thread(target=self.thread)
        control.daemon = True
        control.start()

    def thread(self):
        with Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key):
        if key in mapping:
            super().on_press(mapping[key])

    def on_release(self, key):
        if key in mapping:
            super().on_release(mapping[key])
