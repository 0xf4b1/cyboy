#  SPDX-License-Identifier: GPL-3.0-only

import types

from instructions.cb import *
from instructions.operations import *


class Instructions:
    # opcode -> (len, cycles, fun)
    opcodes = {
        0x0: (1, 4, NOP),
        0x1: (1, 4, STOP),
        0x7: (1, 4, RLCA),
        0x8: (3, 20, LD_a16_SP),
        0xf: (1, 4, RRCA),
        0x10: (1, 4, NOP),
        0x17: (1, 4, RLA),
        0x18: (2, 12, JR),
        0x1f: (1, 4, RRA),
        0x22: (1, 8, LDI_HL_A),
        0x27: (1, 4, DAA),
        0x2a: (1, 8, LDI_A_HL),
        0x2f: (1, 4, CPL),
        0x32: (1, 8, LDD_HL_A),
        0x37: (1, 4, SCF),
        0x3a: (1, 8, LDD_A_HL),
        0x3f: (1, 4, CCF),
        0x76: (1, 4, HALT),
        0xc3: (3, 16, JP_nn),
        0xc9: (1, 16, RET),
        0xcd: (3, 24, CALL),
        0xd3: (1, 4, NOP),
        0xd9: (1, 16, RETI),
        0xdb: (1, 4, NOP),
        0xdd: (1, 4, NOP),
        0xe0: (2, 12, LDH_n_A),
        0xe2: (1, 8, LD_C_A),
        0xe3: (1, 4, NOP),
        0xe4: (1, 4, NOP),
        0xe8: (2, 16, ADD_SP_r8),
        0xe9: (1, 4, JP_HL),
        0xea: (3, 16, LD_a16_A),
        0xeb: (1, 4, NOP),
        0xec: (1, 4, NOP),
        0xed: (1, 4, NOP),
        0xf0: (2, 12, LDH_A_n),
        0xf2: (1, 8, LD_A_C),
        0xf3: (1, 4, DI),
        0xf4: (1, 4, NOP),
        0xf8: (2, 12, LD_HL_SP_r8),
        0xf9: (1, 8, LD_SP_HL),
        0xfa: (3, 16, LD_A_a16),
        0xfb: (1, 4, EI),
        0xfc: (1, 4, NOP),
        0xfd: (1, 4, NOP),
    }

    cb = {}

    registers = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A', 'd8', 'r8', 'a16',
                 'BC', 'DE', 'HL', 'SP', 'AF', 'C', 'a8', 'r8', 'a16', 'd16', '(BC)', '(DE)']

    conds = [
        lambda self: not self.cpu.flag_Z(),
        lambda self: self.cpu.flag_Z(),
        lambda self: not self.cpu.flag_C(),
        lambda self: self.cpu.flag_C()
    ]

    def build(self, gameboy):
        self.cpu = gameboy.cpu
        self.mmu = gameboy.mmu
        self.build_ops()
        self.build_cb()

    def decode(self, inst, cb):
        if cb:
            return self.cb[inst]
        return self.opcodes[inst]

    def build_ops(self):

        # INC, DEC
        for i in range(0x40):
            if i % 8 == 0 and i // 16 > 1:
                self.opcodes[i] = 2, 12, lambda self, value, cond=self.conds[i // 8 - 4]: JR(self, value, cond)
            elif i % 16 == 1:
                self.opcodes[i] = self.build_op(20, i // 16 + 11, LD)
            elif i % 16 == 2 and i // 16 < 2:
                self.opcodes[i] = self.build_op(7, i // 16 + 21, LD)
            elif i % 16 == 3:
                self.opcodes[i] = self.build_op(i // 16 + 11, i // 16 + 11, INC_nn)
            elif i % 16 == 9:
                self.opcodes[i] = self.build_op(i // 16 + 11, 13, lambda self, x: ADD_HL_n(self, self.cpu.HL(), x))
            elif i % 16 == 10 and i // 16 < 2:
                self.opcodes[i] = self.build_op(i // 16 + 21, 7, LD)
            elif i % 16 == 11:
                self.opcodes[i] = self.build_op(i // 16 + 11, i // 16 + 11, DEC_nn)
            elif i % 8 == 4:
                self.opcodes[i] = self.build_op(i // 8, i // 8, INC)
            elif i % 8 == 5:
                self.opcodes[i] = self.build_op(i // 8, i // 8, DEC)
            elif i % 8 == 6:
                self.opcodes[i] = self.build_op(8, i // 8, LD)

        # LD
        for i in range(0x40, 0x80):
            if (i - 0x40) // 8 == 6 and i % 8 == 6:
                # HALT
                continue

            self.opcodes[i] = self.build_op(i % 8, (i - 0x40) // 8, LD)

        ops = [ADD, ADC, SUB, SBC, AND, XOR, OR, CP]
        for i in range(0x80, 0xC0):
            self.opcodes[i] = self.build_op(i % 8, 7, lambda self, x, fun=ops[(i - 0x80) // 8]: fun(self, self.cpu.A, x))

        get_reg16 = [self.cpu.BC, self.cpu.DE, self.cpu.HL, self.cpu.AF]
        set_reg16 = [self.cpu.set_BC, self.cpu.set_DE, self.cpu.set_HL, self.cpu.set_AF]

        for i in range(0xC0, 0x100):

            if i % 8 == 0 and (i - 0xC0) // 8 < 4:
                self.opcodes[i] = 1, 12, lambda self, cond=self.conds[(i - 0xC0) // 8]: RET(self, cond)
            elif i % 8 == 2 and (i - 0xC0) // 8 < 4:
                self.opcodes[i] = 3, 12, lambda self, value, cond=self.conds[(i - 0xC0) // 8]: JP(self, value, cond)
            elif i % 8 == 4 and (i - 0xC0) // 8 < 4:
                self.opcodes[i] = 3, 12, lambda self, value, cond=self.conds[(i - 0xC0) // 8]: CALL(self, value, cond)
            elif i % 16 == 1:
                self.opcodes[i] = 1, 12, lambda self, fun=set_reg16[i // 16 - 12]: fun(POP(self))
            elif i % 16 == 5:
                self.opcodes[i] = 1, 12, lambda self, fun=get_reg16[i // 16 - 12]: PUSH(self, fun())
            elif i % 8 == 6:
                # XXX A,d8
                self.opcodes[i] = self.build_op(8, 7, lambda self, x, fun=ops[((i - 0xC0) // 8)]: fun(self, self.cpu.A, x))
            elif i % 8 == 7:
                # RST XXX
                self.opcodes[i] = 1, 16, lambda self, addr=(((i - 0xC0) // 7) - 1) * 8: RST(self, addr)

    def build_cb(self):
        ops = [RLC, RRC, RL, RR, SLA, SRA, SWAP, SRL, BIT, RES, SET]
        for i in range(0x40):
            self.cb[i] = self.build_op(i % 8, i % 8, ops[i // 8])

        ops = [BIT, RES, SET]
        for i in range(0x40, 0x100):
            self.cb[i] = self.build_op(i % 8, i % 8, lambda self, value, fun=ops[(i // 0x40) - 1], param=(i % 0x40) // 8: fun(self, value, param))

    def build_op(self, src, dst, fun):
        src = self.registers[src]
        dst = self.registers[dst]
        src_fun = self.getter_fun(src)
        dst_fun = self.setter_fun(dst)

        if '8' in src:
            return 2, 8, lambda self, value: dst_fun(self, fun(self, value))
        elif '8' in dst:
            return 2, 8, lambda self, value: dst_fun(self, value, fun(self, src_fun(self)))
        elif '16' in src:
            return 3, 12, lambda self, value: dst_fun(self, fun(self, value))
        elif '16' in dst:
            return 3, 12, lambda self, value: dst_fun(self, value, fun(self, src_fun(self)))

        return 1, 4, lambda self: dst_fun(self, fun(self, src_fun(self)))

    def getter_fun(self, src):
        mem = src.startswith('(') and src.endswith(')')
        if mem:
            src = src[1:-1]

        if not hasattr(self.cpu, src):
            if not mem:
                return lambda self, value: value
            else:
                return lambda self, value: self.mmu.read(value)

        fun = getattr(self.cpu, src)
        if not isinstance(fun, types.MethodType):
            fun = lambda self: getattr(self.cpu, src)
        else:
            fun = lambda self: getattr(self.cpu, src)()

        if mem:
            return lambda self: self.mmu.read(fun(self))
        else:
            return fun

    def setter_fun(self, dst):
        if dst.startswith('(') and dst.endswith(')'):
            fun = self.getter_fun(dst[1:-1])
            return lambda self, value: self.mmu.write(fun(self), value)

        attr = getattr(self.cpu, dst)
        if not isinstance(attr, types.MethodType):
            return lambda self, value: setattr(self.cpu, dst, value)
        else:
            dst = 'set_' + dst
            return lambda self, value: getattr(self.cpu, dst)(value)
