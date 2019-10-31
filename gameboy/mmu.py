#  SPDX-License-Identifier: GPL-3.0-only

import random

from gameboy.mbc import MBC

"""
General Memory Map
  0000-3FFF   16KB ROM Bank 00     (in cartridge, fixed at bank 00)
  4000-7FFF   16KB ROM Bank 01..NN (in cartridge, switchable bank number)
  8000-9FFF   8KB Video RAM (VRAM) (switchable bank 0-1 in CGB Mode)
  A000-BFFF   8KB External RAM     (in cartridge, switchable bank, if any)
  C000-CFFF   4KB Work RAM Bank 0 (WRAM)
  D000-DFFF   4KB Work RAM Bank 1 (WRAM)  (switchable bank 1-7 in CGB Mode)
  E000-FDFF   Same as C000-DDFF (ECHO)    (typically not used)
  FE00-FE9F   Sprite Attribute Table (OAM)
  FEA0-FEFF   Not Usable
  FF00-FF7F   I/O Ports
  FF80-FFFE   High RAM (HRAM)
  FFFF        Interrupt Enable Register
"""


class MMU:

    def __init__(self, gameboy, args):
        self.controls = gameboy.controls
        self.mbc = MBC(args.rom)

    ram = bytearray(0x10000)  # 0x0000-0xFFFF

    def load_rom(self, rom):
        """
        Load GameBoy cartridge (ROM)
        At the moment only type 0 (ROM only) supported, with two ROM Banks:
        16KB Rom Bank 00 and 16KB Rom Bank 01 directly mapped into memory
        :param rom: path to rom file
        """
        with open(rom, 'rb') as file:
            self.ram[0x0000:0x7FFF] = file.read()

    def read(self, addr):
        if addr == 0xFF04:
            return random.randint(0, 0xFF)

        if addr in range(0x7FFF):
            return self.mbc.read(addr)

        return self.ram[addr]

    def write(self, addr, value):
        # cartridge controls
        if addr in range(0x2000, 0x7FFF):
            self.mbc.write(addr, value)
            return

        if addr not in range(0x8000, 0x10000):
            return

        if addr == 0xFF00:
            # controls
            buttons = value >> 5 & 1 == 0
            directions = value >> 4 & 1 == 0

            if buttons and not directions:
                value |= self.controls.states >> 4
            elif directions and not buttons:
                value |= self.controls.states & 0xF
            else:
                value |= 0xF

        elif addr == 0xFF46:
            # LCD OAM DMA Transfer
            self.ram[0xFE00:0xFE9F] = self.ram[value << 8:(value << 8) | 0x9F]

        self.ram[addr] = value

    def set_mode(self, mode):
        """
        FF41 - STAT - LCDC Status (R/W)
          Bit 6 - LYC=LY Coincidence Interrupt (1=Enable) (Read/Write)
          Bit 5 - Mode 2 OAM Interrupt         (1=Enable) (Read/Write)
          Bit 4 - Mode 1 V-Blank Interrupt     (1=Enable) (Read/Write)
          Bit 3 - Mode 0 H-Blank Interrupt     (1=Enable) (Read/Write)
          Bit 2 - Coincidence Flag  (0:LYC<>LY, 1:LYC=LY) (Read Only)
          Bit 1-0 - Mode Flag       (Mode 0-3, see below) (Read Only)
                    0: During H-Blank
                    1: During V-Blank
                    2: During Searching OAM-RAM
                    3: During Transfering Data to LCD Driver
        """

        value = self.ram[0xFF41] & 3  # get 2-LSB
        mask = value ^ mode  # XOR with target mode
        self.write(0xFF41, self.read(0xFF41) ^ mask)

    def set_coincidence_flag(self, set):
        if set:
            self.write(0xFF41, self.read(0xFF41) | (1 << 2))
        else:
            self.write(0xFF41, self.read(0xFF41) & ~(1 << 2))

    def coincidence_interrupt(self):
        return self.read(0xFF41) >> 6 & 1

    def lcdc(self):
        return self.read(0xFF40)

    def bg_tile_map_display_select(self):
        return self.lcdc() >> 3 & 1

    def bg_window_tile_data_select(self):
        return self.lcdc() >> 4 & 1

    def lcd_display_enable(self):
        return self.lcdc() >> 7 & 1

    def ly(self):
        return self.read(0xFF44)

    def set_ly(self, y):
        """
        FF44 - LY - LCDC Y-Coordinate (R) The LY indicates the vertical line to which the present data is transferred
        to the LCD Driver. The LY can take on any value between 0 through 153. The values between 144 and 153
        indicate the V-Blank period. Writing will reset the counter.

        :param y: y coordinate
        """

        self.write(0xFF44, y)
        self.check_lyc_ly_coincidence()

    def lyc(self):
        return self.read(0xFF45)

    def check_lyc_ly_coincidence(self):
        if self.lyc() == self.ly():
            self.set_coincidence_flag(True)
            if self.coincidence_interrupt():
                self.set_lcd_stat()
        else:
            self.set_coincidence_flag(False)

    def scy(self):
        return self.read(0xFF42)

    def scx(self):
        return self.read(0xFF43)

    def wy(self):
        return self.read(0xFF4A)

    def wx(self):
        return self.read(0xFF4B)

    def tile_data_addr(self):
        return 0x8000 if self.bg_window_tile_data_select() else 0x9000

    def bg_map_addr(self):
        return 0x9C00 if self.bg_tile_map_display_select() else 0x9800

    def get_bg_tile(self, x, y):
        tile = self.ram[self.bg_map_addr() + y * 32 + x]

        if not self.bg_window_tile_data_select() or self.bg_tile_map_display_select():
            # convert to signed
            tile = (tile ^ 0x80) - 128

        return self.tile_data_addr() + tile * 16

    def set_vblank(self):
        self.set_interrupt(0)

    def set_lcd_stat(self):
        self.set_interrupt(1)

    def set_interrupt(self, value):
        self.write(0xFF0F, self.read(0xFF0F) | (1 << value))
