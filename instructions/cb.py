#  SPDX-License-Identifier: GPL-3.0-only


def RLC(self, value):
    """
    5. RLC n
        Description:
         Rotate n left. Old bit 7 to Carry flag.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
        Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 7 data.
    """

    c = (value >> 7) & 1
    value = ((value << 1) | c) & 0xFF
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def RRC(self, value):
    """
    7. RRC n
        Description:
         Rotate n right. Old bit 0 to Carry flag.
        Use with:
        n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 0 data
    """

    c = value & 1
    value = ((value >> 1) | (c << 7)) & 0xFF
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def RL(self, value):
    """
    6. RL n
        Description:
         Rotate n left through Carry flag.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 7 data.
    """

    c = (value >> 7) & 1
    value = ((value << 1) | self.cpu.flag_C()) & 0xFF
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def RR(self, value):
    """
    8. RR n
        Description:
         Rotate n right through Carry flag.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 0 data.
    """

    c = value & 1
    value = ((value >> 1) | (self.cpu.flag_C() << 7)) & 0xFF
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def SLA(self, value):
    """
    9. SLA n
        Description:
         Shift n left into Carry. LSB of n set to 0.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 7 data.
    """

    c = value >> 7 & 1
    value = value << 1 & 0xFF
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def SRA(self, value):
    """
    10. SRA n
        Description:
         Shift n right into Carry. MSB doesn't change.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 0 data.
    """

    c = value & 1
    value = (value >> 1 | value & (1 << 7)) & 0xFF
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def SWAP(self, value):
    """
    1. SWAP n
        Description:
         Swap upper & lower nibles of n.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Reset.
    """
    res = (value << 4 | value >> 4) & 0xFF
    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(False)
    return res


def SRL(self, value):
    """
    11. SRL n
        Description:
         Shift n right into Carry. MSB set to 0.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 0 data
    """

    c = value & 1
    value = value >> 1
    self.cpu.set_flag_Z(value == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)
    return value


def BIT(self, value, i):
    """
    1. BIT b,r
        Description:
         Test bit b in register r.
        Use with:
         b = 0 - 7, r = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if bit b of register r is 0.
         N - Reset.
         H - Set.
         C - Not affected.
    """
    self.cpu.set_flag_Z(value >> i & 1 == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(True)
    return value


def RES(self, value, i):
    """
    3. RES b,r
        Description:
         Reset bit b in register r.
        Use with:
         b = 0 - 7, r = A,B,C,D,E,H,L,(HL)
        Flags affected:
         None.
    """
    return value & ~(1 << i)


def SET(self, value, i):
    """
    2. SET b,r
        Description:
         Set bit b in register r.
        Use with:
         b = 0 - 7, r = A,B,C,D,E,H,L,(HL)
        Flags affected:
         None.
    """
    return value | 1 << i
