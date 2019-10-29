#  SPDX-License-Identifier: GPL-3.0-only

import argparse

from controls.controls_keyboard import KeyboardControls
from display.display_curses import CursesDisplay
from gameboy.cpu import CPU
from gameboy.mmu import MMU


class CyBoy:

    def __init__(self, args):
        self.controls = KeyboardControls()
        self.mmu = MMU(self, args)
        self.display = CursesDisplay(self, args.overlay)
        self.cpu = CPU(self)

    def start(self):
        self.cpu.instructions.build(self)

        # main-loop
        while 1:
            self.cpu.next_frame()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CyBoy - An experimental gameboy emulator')
    parser.add_argument('rom', type=str, help='ROM file')
    parser.add_argument('--overlay', dest='overlay', default=False, action='store_true',
                        help='Show overlay with FPS')

    args = parser.parse_args()

    gameboy = CyBoy(args)
    gameboy.start()
