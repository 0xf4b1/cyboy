#  SPDX-License-Identifier: GPL-3.0-only


class MBC:
    rom_bank_number = 0x01  # 0x01-0x7F (7 bit)
    ram_bank_number = 0  # 0x00-0x03 (2 bit)
    rom_ram_select = 0  # 1 bit

    def __init__(self, path):
        with open(path, 'rb') as file:
            self.rom = bytearray(file.read())

        self.title = self.rom[0x134:0x0143].decode('ascii')
        self.type = self.rom[0x147]
        self.rom_size = self.rom[0x148]
        self.ram_size = self.rom[0x149]

    def read(self, addr):
        if addr in range(0x4000):
            return self.rom[addr]
        if addr in range(0x4000, 0x7FFF):
            return self.rom[(self.rom_bank_number - 1) * 0x4000 + addr]

    def write(self, addr, value):
        if addr in range(0x2000, 0x3FFF):
            self.rom_bank_number = max(1, value)

        elif addr in range(0x4000, 0x5FFF):
            self.ram_bank_number = value

        elif addr in range(0x6000, 0x7FFF):
            self.rom_ram_select = value

    def __str__(self):
        return 'Title: {}\n' \
               'Cartridge Type: {}\n' \
               'ROM Size: {}\n' \
               'RAM Size: {}'.format(self.title, self.type, self.rom_size, self.ram_size)
