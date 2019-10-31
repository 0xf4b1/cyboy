#  SPDX-License-Identifier: GPL-3.0-only

from instructions.instructions import Instructions


class CPU:
    # 8 bit registers
    B, C, D, E, H, L, A, F = [0 for i in range(8)]

    SP = 0
    PC = 0

    ime = True

    def __init__(self, gameboy):
        self.gameboy = gameboy
        self.mmu = gameboy.mmu
        self.display = gameboy.display
        self.instructions = Instructions()

    def next_frame(self):
        """
        Resolution   - 160x144 (20x18 tiles)
        """
        if not self.mmu.lcd_display_enable():
            self.mmu.set_mode(0)
            self.mmu.set_ly(0)

            for i in range(154):
                self.next_instructions(456)
            return

        # 144 vertical lines
        for i in range(144):
            self.mmu.set_ly(i)

            # MODE 2
            # 77-83 clks
            self.mmu.set_mode(2)
            self.next_instructions(80)

            # MODE 3
            # 169-175 clks
            self.mmu.set_mode(3)
            self.next_instructions(172)
            self.display.params[i] = (self.mmu.scy(), self.mmu.scx(), self.mmu.wy(), self.mmu.wx())

            # MODE 0
            # 201-207 clks
            self.mmu.set_mode(0)
            self.next_instructions(204)

        self.mmu.set_vblank()
        self.display.draw()

        for i in range(144, 153):
            self.mmu.set_ly(i)
            # MODE 1
            # 4560 clks
            self.mmu.set_mode(1)
            self.next_instructions(456)

    def read_next(self):
        value = self.mmu.read(self.PC)
        self.PC = (self.PC + 1) & 0xFFFF
        return value

    def next_instruction(self):

        # check interrupts
        self.check_interrupt()

        cb = False

        # fetch instruction
        inst = self.read_next()
        if '%X' % inst == 'CB':
            cb = True
            inst = self.read_next()

        # decode
        length, cycles, op = self.instructions.decode(inst, cb)

        # execute
        if length == 1:
            op(self.gameboy)

        elif length == 2:
            param = self.read_next()
            op(self.gameboy, param)

        elif length == 3:
            v1 = self.read_next()
            v2 = self.read_next()

            param = (v2 << 8) + v1

            op(self.gameboy, param)

        return cycles

    def next_instructions(self, cycles):
        while cycles > 0:
            cycles -= self.next_instruction()

    def check_interrupt(self):
        """
        FFFF - IE - Interrupt Enable (R/W)
          Bit 0: V-Blank  Interrupt Enable  (INT 40h)  (1=Enable)
          Bit 1: LCD STAT Interrupt Enable  (INT 48h)  (1=Enable)
          Bit 2: Timer    Interrupt Enable  (INT 50h)  (1=Enable)
          Bit 3: Serial   Interrupt Enable  (INT 58h)  (1=Enable)
          Bit 4: Joypad   Interrupt Enable  (INT 60h)  (1=Enable)

        FF0F - IF - Interrupt Flag (R/W)
          Bit 0: V-Blank  Interrupt Request (INT 40h)  (1=Request)
          Bit 1: LCD STAT Interrupt Request (INT 48h)  (1=Request)
          Bit 2: Timer    Interrupt Request (INT 50h)  (1=Request)
          Bit 3: Serial   Interrupt Request (INT 58h)  (1=Request)
          Bit 4: Joypad   Interrupt Request (INT 60h)  (1=Request)
        """

        if not self.ime:
            return

        interrupt_enable = self.mmu.ram[0xFFFF]
        interrupt_flag = self.mmu.ram[0xFF0F]

        for i in range(5):

            # check for interrupt enable and interrupt request being set
            if interrupt_enable >> i & 1 and interrupt_flag >> i & 1:
                # reset corresponding bit
                self.mmu.ram[0xFF0F] &= ~(1 << i)

                # disable IME
                self.ime = False

                # push PC to stack
                self.mmu.write(self.SP - 1, self.PC >> 8)
                self.mmu.write(self.SP - 2, self.PC & 0xFF)
                self.SP -= 2

                # call corresponding interrupt address
                self.PC = 0x40 + i * 8

    def AF(self):
        return (self.A << 8) + self.F

    def set_AF(self, value):
        self.A, self.F = self.set_NN(value)
        self.F &= 0xF0

    def BC(self):
        return (self.B << 8) + self.C

    def set_BC(self, value):
        self.B, self.C = self.set_NN(value)

    def DE(self):
        return (self.D << 8) + self.E

    def set_DE(self, value):
        self.D = value >> 8 & 0xFF
        self.E = value & 0xFF

    def HL(self):
        return (self.H << 8) + self.L

    def set_HL(self, value):
        self.H = value >> 8 & 0xFF
        self.L = value & 0xFF

    def NN(self, first, second):
        return (first << 8) + second

    def set_NN(self, value):
        first = value >> 8 & 0xFF
        second = value & 0xFF
        return first, second

    flags = {
        'Z': 7,
        'N': 6,
        'H': 5,
        'C': 4
    }

    def flag_Z(self):
        return self.get_bit(self.flags['Z'])

    def set_flag_Z(self, true):
        self.set_bit(self.flags['Z'], true)

    def flag_N(self):
        return self.get_bit(self.flags['N'])

    def set_flag_N(self, true):
        self.set_bit(self.flags['N'], true)

    def flag_H(self):
        return self.get_bit(self.flags['H'])

    def set_flag_H(self, true):
        self.set_bit(self.flags['H'], true)

    def flag_C(self):
        return self.get_bit(self.flags['C'])

    def set_flag_C(self, true):
        self.set_bit(self.flags['C'], true)

    def get_bit(self, i):
        return self.F >> i & 1

    def set_bit(self, i, true):
        if true:
            self.F |= 1 << i
        else:
            self.F &= ~(1 << i)
