#  SPDX-License-Identifier: GPL-3.0-only

RIGHT, LEFT, UP, DOWN, A, B, SELECT, START = range(8)


class Controls:
    states = 0xFF

    def on_press(self, key):
        self.states &= ~(1 << key)

    def on_release(self, key):
        self.states |= (1 << key)
