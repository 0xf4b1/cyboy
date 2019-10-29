#  SPDX-License-Identifier: GPL-3.0-only

import time

WIDTH, HEIGHT = 160, 144


class Display:

    def __init__(self, gameboy):
        self.mmu = gameboy.mmu
        self.screenbuffer = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
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

            # hidden sprites
            # don't draw sprites that are off-screen
            if y < 0 or y > 144 or x < 0 or x > 160:
                continue

            self.draw_tile(x, y, 0x8000 + tile * 16, sprite=True)

    def draw_bg(self):
        """
        Draw 256x256 background image that consists of 32x32 tiles with size 8x8 px
        """

        for y in range(32):
            for x in range(32):
                self.draw_tile(x * 8, y * 8, self.mmu.get_bg_tile(x, y))

    def draw_tile(self, start_x, start_y, tile_addr, sprite=False):
        """
        Draw 8x8 tile
        """

        tile = self.mmu.ram[tile_addr:tile_addr + 16]
        palette = self.mmu.read(0xFF47)

        for y in range(8):
            for x in range(8):

                if y + start_y >= HEIGHT or x + start_x >= WIDTH:
                    continue

                color = ((tile[y * 2] >> (7 - x)) & 1) << 1 | ((tile[y * 2 + 1] >> (7 - x)) & 1)

                color = (palette >> (color * 2)) & 3

                # sprite is transparent instead white
                if color == 0 and sprite:
                    continue

                self.screenbuffer[y + start_y][x + start_x] = color
