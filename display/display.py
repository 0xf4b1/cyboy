#  SPDX-License-Identifier: GPL-3.0-only

import time

WIDTH, HEIGHT = 160, 144


class Display:

    def __init__(self, gameboy):
        self.mmu = gameboy.mmu
        self.screenbuffer = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.background = [[0 for _ in range(256)] for _ in range(256)]
        self.params = [(0, 0, 0, 0) for _ in range(256)]
        self.count, self.fps = 0, 0
        self.time = time.time()

    def render(self, screenbuffer):
        raise NotImplementedError('render not implemented!')

    def draw(self):
        self.draw_bg()
        self.draw_sprites()
        self.render(self.screenbuffer)
        self.count_frame()

    def count_frame(self):
        self.count += 1
        if self.time + 1 < time.time():
            self.fps = self.count
            self.count = 0
            self.time = time.time()

    def draw_bg(self):
        """
        Draw 256x256 background image that consists of 32x32 tiles with size 8x8 px
        """

        for y in range(32):
            for x in range(32):
                self.draw_bg_tile(x * 8, y * 8, self.mmu.get_bg_tile(x, y))

        self.draw_visible_bg_area()

    def draw_bg_tile(self, offset_x, offset_y, tile_addr):
        tile = self.mmu.ram[tile_addr:tile_addr + 16]
        palette = self.mmu.ram[0xFF47]

        for y in range(8):
            for x in range(8):
                color = ((tile[y * 2] >> (7 - x)) & 1) << 1 | ((tile[y * 2 + 1] >> (7 - x)) & 1)

                color = (palette >> (color * 2)) & 3

                self.background[y + offset_y][x + offset_x] = color

    def draw_visible_bg_area(self):
        for y in range(HEIGHT):
            scy, scx, wy, wx = self.params[y]

            for x in range(WIDTH):
                color = self.background[(y + scy) % 256][(x + scx) % 256]
                self.screenbuffer[y][x] = color

    def draw_sprites(self):
        """
        GameBoy video controller can display up to 40 sprites either in 8x8 or in 8x16 pixels. Because of a limitation
        of hardware, only ten sprites can be displayed per scan line. Sprite patterns have the same format as BG tiles,
        but they are taken from the Sprite Pattern Table located at $8000-8FFF and have unsigned numbering.
        Sprite attributes reside in the Sprite Attribute Table (OAM - Object Attribute Memory) at $FE00-FE9F.
        """

        for i in range(0xFE00, 0xFE9F, 4):
            y = self.mmu.read(i) - 16
            x = self.mmu.read(i + 1) - 8
            tile = self.mmu.read(i + 2)
            attr = self.mmu.read(i + 3)
            x_flip = attr >> 5 & 1
            y_flip = attr >> 6 & 1

            # hidden sprites
            # don't draw sprites that are off-screen
            if y < 0 or y > 144 or x < 0 or x > 160:
                continue

            self.draw_tile(x, y, 0x8000 + tile * 16, x_flip, y_flip)

    def draw_tile(self, offset_x, offset_y, tile_addr, x_flip, y_flip):
        """
        Draw 8x8 tile
        """

        tile = self.mmu.ram[tile_addr:tile_addr + 16]
        palette = self.mmu.read(0xFF48)

        for y in range(8):
            for x in range(8):

                if y + offset_y >= HEIGHT or x + offset_x >= WIDTH:
                    continue

                color = ((tile[(y if not y_flip else (7 - y)) * 2] >> ((7 - x) if not x_flip else x)) & 1) << 1 | (
                            (tile[(y if not y_flip else (7 - y)) * 2 + 1] >> ((7 - x) if not x_flip else x)) & 1)

                color = (palette >> (color * 2)) & 3

                # sprite is transparent instead white
                if color == 0:
                    continue

                self.screenbuffer[y + offset_y][x + offset_x] = color
