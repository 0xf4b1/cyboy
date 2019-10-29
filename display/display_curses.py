#  SPDX-License-Identifier: GPL-3.0-only

import curses

from display.display import Display

colors = {0: '\u2588\u2588',
          1: '\u2592\u2592',
          2: '\u2593\u2593',
          3: '  '}


class CursesDisplay(Display):

    def __init__(self, gameboy, overlay=False):
        super().__init__(gameboy)
        self.gameboy = gameboy
        self.overlay = overlay
        self.scr = curses.initscr()

        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)

    def render(self, screenbuffer, overlay=False):
        for y in range(min(len(screenbuffer), curses.LINES - 1)):
            self.scr.addstr(y, 0, "".join(
                colors[screenbuffer[y][x]] for x in range(min(len(screenbuffer[0]), curses.COLS - 1))))

        if self.overlay:
            self.scr.addstr(0, 0, "FPS: {}".format(self.gameboy.display.fps), curses.color_pair(1))

        self.scr.refresh()
