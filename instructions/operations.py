#  SPDX-License-Identifier: GPL-3.0-only


def sign(value):
    return (value ^ 0x80) - 0x80


def NOP(self):
    """
    6. NOP
        Description:
         No operation.
    """
    pass


def STOP(self):
    """
    8. STOP
        Description:
         Halt CPU & LCD display until button pressed.
    """
    # logging.warning("STOP called")
    pass


def HALT(self):
    """
    7. HALT
        Description:
         Power down CPU until an interrupt occurs. Use this
         when ever possible to reduce energy consumption.
    """
    # logging.warning("HALT called")
    pass


def PUSH(self, value):
    """
    6. PUSH nn
        Description:
         Push register pair nn onto stack.
         Decrement Stack Pointer (SP) twice.
        Use with:
         nn = AF,BC,DE,HL
    """
    self.mmu.write(self.cpu.SP - 1, value >> 8)
    self.mmu.write(self.cpu.SP - 2, value & 0xFF)
    self.cpu.SP -= 2


def POP(self):
    """
    7. POP nn
        Description:
         Pop two bytes off stack into register pair nn.
         Increment Stack Pointer (SP) twice.
        Use with:
         nn = AF,BC,DE,HL
    """
    value = (self.mmu.read(self.cpu.SP + 1) << 8 | self.mmu.read(self.cpu.SP)) & 0xFFFF
    self.cpu.SP += 2
    return value


def JP(self, value, cond=None):
    """
    1. JP nn
        Description:
         Jump to address nn.
        Use with:
         nn = two byte immediate value. (LS byte first.)
    """
    if not cond or cond(self):
        self.cpu.PC = value


def JP_HL(self):
    """
    3. JP (HL)
        Description:
         Jump to address contained in HL.
    """
    self.cpu.PC = self.cpu.HL()


def JP_nn(self, addr):
    """
    1. JP nn
        Description:
         Jump to address nn.
        Use with:
         nn = two byte immediate value. (LS byte first.)
    """
    self.cpu.PC = addr


def JR(self, value, cond=None):
    """
    4. JR n
        Description:
         Add n to current address and jump to it.
        Use with:
         n = one byte signed immediate value
    """
    if not cond or cond(self):
        self.cpu.PC = (self.cpu.PC + sign(value)) & 0xFFFF


def CALL(self, addr, cond=None):
    """
    1. CALL nn
        Description:
         Push address of next instruction onto stack and then
         jump to address nn.
        Use with:
         nn = two byte immediate value. (LS byte first.)
    """
    if not cond or cond(self):
        PUSH(self, self.cpu.PC)
        self.cpu.PC = addr


def RET(self, cond=None):
    """
    1. RET
        Description:
         Pop two bytes from stack & jump to that address.
    """
    if not cond or cond(self):
        self.cpu.PC = POP(self)


def RETI(self):
    """
    3. RETI
        Description:
         Pop two bytes from stack & jump to that address then
         enable interrupts.
    """
    self.cpu.PC = POP(self)
    self.cpu.ime = True


def RST(self, addr):
    """
    1. RST n
        Description:
         Push present address onto stack.
         Jump to address $0000 + n.
        Use with:
         n = $00,$08,$10,$18,$20,$28,$30,$38
    """
    PUSH(self, self.cpu.PC)
    self.cpu.PC = addr


def INC(self, reg):
    """
    9. INC n
        Description:
         Increment register n.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Set if carry from bit 3.
         C - Not affected.
    """
    self.cpu.set_flag_H((reg & 0xF) + 1 > 0xF)

    reg = (reg + 1) & 0xFF

    self.cpu.set_flag_Z(reg == 0)
    self.cpu.set_flag_N(False)

    return reg


def INC_nn(self, reg):
    """
    3. INC nn
        Description:
         Increment register nn.
        Use with:
         nn = BC,DE,HL,SP
        Flags affected:
         None.
    """
    return (reg + 1) & 0xFFFF


def DEC(self, reg):
    """
    10. DEC n
        Description:
         Decrement register n.
        Use with:
         n = A,B,C,D,E,H,L,(HL)
        Flags affected:
         Z - Set if result is zero.
         N - Set.
         H - Set if no borrow from bit 4.
         C - Not affected.
    """
    self.cpu.set_flag_H((reg & 0xF) - 1 < 0)

    reg = (reg - 1) & 0xFF

    self.cpu.set_flag_Z(reg == 0)
    self.cpu.set_flag_N(True)

    return reg


def DEC_nn(self, value):
    """
    4. DEC nn
        Description:
         Decrement register nn.
        Use with:
         nn = BC,DE,HL,SP
        Flags affected:
         None.
    """
    return (value - 1) & 0xFFFF


def ADD(self, a, b):
    """
    1. ADD A,n
        Description:
         Add n to A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Set if carry from bit 3.
         C - Set if carry from bit 7.
    """
    res = (a + b) & 0xFF

    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H((a & 0xF) + (b & 0xF) > 0xF)
    self.cpu.set_flag_C(a + b > 0xFF)

    return res


def ADD_HL_n(gameboy, a, b):
    """
    1. ADD HL,n
        Description:
         Add n to HL.
        Use with:
         n = BC,DE,HL,SP
        Flags affected:
         Z - Not affected.
         N - Reset.
         H - Set if carry from bit 11.
         C - Set if carry from bit 15.
    """
    res = (a + b) & 0xFFFF

    gameboy.cpu.set_flag_N(False)
    gameboy.cpu.set_flag_H((a & 0xFFF) + (b & 0xFFF) > 0xFFF)
    gameboy.cpu.set_flag_C(a + b > 0xFFFF)

    return res


def ADD_SP_r8(self, value):
    """
    2. ADD SP,n
        Description:
         Add n to Stack Pointer (SP).
        Use with:
         n = one byte signed immediate value (#).
        Flags affected:
         Z - Reset.
         N - Reset.
         H - Set or reset according to operation.
         C - Set or reset according to operation.
    """
    value = sign(value)
    res = (self.cpu.SP + value) & 0xFFFF

    self.cpu.set_flag_Z(False)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H((self.cpu.SP & 0xF) + (value & 0xF) > 0xF)
    self.cpu.set_flag_C((self.cpu.SP & 0xFF) + (value & 0xFF) > 0xFF)

    self.cpu.SP = res


def ADC(self, a, b):
    """
    2. ADC A,n
        Description:
         Add n + Carry flag to A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Set if carry from bit 3.
         C - Set if carry from bit 7.
    """
    res = a + b + self.cpu.flag_C()

    self.cpu.set_flag_Z(res & 0xFF == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H((a & 0xF) + (b & 0xF) + self.cpu.flag_C() > 0xF)
    self.cpu.set_flag_C(res > 0xFF)

    return res & 0xFF


def SUB(self, a, b):
    """
    3. SUB n
        Description:
         Subtract n from A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Set.
         H - Set if no borrow from bit 4.
         C - Set if no borrow.
    """
    res = (a - b) & 0xFF

    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(True)
    self.cpu.set_flag_H((a & 0xF) < (b & 0xF))
    self.cpu.set_flag_C(a < b)

    return res


def SBC(self, a, b):
    """
    4. SBC A,n
        Description:
         Subtract n + Carry flag from A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Set.
         H - Set if no borrow from bit 4.
         C - Set if no borrow.
    """
    res = (a - b - self.cpu.flag_C()) & 0xFF

    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(True)
    self.cpu.set_flag_H((a & 0xF) < (b & 0xF) + self.cpu.flag_C())
    self.cpu.set_flag_C(a < b + self.cpu.flag_C())

    return res


def AND(self, a, b):
    """
    5. AND n
        Description:
         Logically AND n with A, result in A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Set.
         C - Reset.
    """
    res = a & b
    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(True)
    self.cpu.set_flag_C(False)
    return res


def OR(self, a, b):
    """
    6. OR n
        Description:
         Logical OR n with register A, result in A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Reset.
    """
    res = a | b
    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(False)
    return res


def XOR(self, a, b):
    """
    7. XOR n
        Description:
         Logical exclusive OR n with register A, result in A.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Reset.
    """
    res = a ^ b
    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(False)
    return res


def CP(self, a, b):
    """
    8. CP n
        Description:
         Compare A with n. This is basically an A - n
         subtraction instruction but the results are thrown
         away.
        Use with:
         n = A,B,C,D,E,H,L,(HL),#
        Flags affected:
         Z - Set if result is zero. (Set if A = n.)
         N - Set.
         H - Set if no borrow from bit 4.
         C - Set for no borrow. (Set if A < n.)
    """
    res = a - b
    self.cpu.set_flag_Z(res == 0)
    self.cpu.set_flag_N(True)
    self.cpu.set_flag_H((a & 0xF) - (b & 0xF) < 0)
    self.cpu.set_flag_C(res < 0)
    return a


def LD(self, value):
    """
    1. LD nn,n
        Description:
         Put value nn into n.
        Use with:
         nn = B,C,D,E,H,L,BC,DE,HL,SP
         n = 8 bit immediate value
    """
    return value


def RLCA(self):
    """
    1. RLCA
        Description:
         Rotate A left. Old bit 7 to Carry flag.
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 7 data.
    """
    c = (self.cpu.A >> 7) & 1
    self.cpu.A = ((self.cpu.A << 1) | c) & 0xFF
    self.cpu.set_flag_Z(False)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)


def RRCA(self):
    """
    3. RRCA
        Description:
         Rotate A right. Old bit 0 to Carry flag.
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 0 data.
    """

    c = self.cpu.A & 1
    self.cpu.A = ((self.cpu.A >> 1) | c << 7) & 0xFF
    self.cpu.set_flag_Z(False)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)


def RLA(self):
    """
    2. RLA
        Description:
         Rotate A left through Carry flag.
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 7 data.
    """

    c = (self.cpu.A >> 7) & 1
    self.cpu.A = ((self.cpu.A << 1) | self.cpu.flag_C()) & 0xFF
    self.cpu.set_flag_Z(False)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)


def RRA(self):
    """
    RRA
        Description:
         Rotate A right through Carry flag.
        Flags affected:
         Z - Set if result is zero.
         N - Reset.
         H - Reset.
         C - Contains old bit 0 data.
    """
    c = self.cpu.A & 1
    self.cpu.A = ((self.cpu.A >> 1) | (self.cpu.flag_C() << 7)) & 0xFF
    self.cpu.set_flag_Z(False)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(c)


def DAA(self):
    """
    2. DAA
        Description:
         Decimal adjust register A.
         This instruction adjusts register A so that the
         correct representation of Binary Coded Decimal (BCD)
         is obtained.
        Flags affected:
         Z - Set if register A is zero.
         N - Not affected.
         H - Reset.
         C - Set or reset according to operation.
    """
    t = self.cpu.A
    corr = 0
    corr |= 0x06 if self.cpu.flag_H() else 0x00
    corr |= 0x60 if self.cpu.flag_C() else 0x00
    if self.cpu.flag_N():
        t -= corr
    else:
        corr |= 0x06 if (t & 0x0F) > 0x09 else 0x00
        corr |= 0x60 if t > 0x99 else 0x00
        t += corr

    self.cpu.set_flag_Z((t & 0xFF) == 0)
    self.cpu.set_flag_H(False)
    self.cpu.set_flag_C(corr & 0x60 != 0)

    t &= 0xFF
    self.cpu.A = t
    self.cpu.A &= 0xFF


def CPL(self):
    """
    3. CPL
        Description:
         Complement A register. (Flip all bits.)
        Flags affected:
         Z - Not affected.
         N - Set.
         H - Set.
         C - Not affected.
    """
    self.cpu.A = ~self.cpu.A & 0xFF
    self.cpu.set_flag_N(True)
    self.cpu.set_flag_H(True)


def SCF(self):
    """
    5. SCF
        Description:
         Set Carry flag.
        Flags affected:
         Z - Not affected.
         N - Reset.
         H - Reset.
         C - Set.
    """
    self.cpu.set_flag_C(True)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)


def CCF(self):
    """
    4. CCF
        Description:
         Complement carry flag.
         If C flag is set, then reset it.
         If C flag is reset, then set it.
        Flags affected:
         Z - Not affected.
         N - Reset.
         H - Reset.
         C - Complemented.
    """
    self.cpu.set_flag_C(not self.cpu.flag_C())
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H(False)


def LDI_HL_A(self):
    """
    18. LDI (HL),A
        Description:
         Put A into memory address HL. Increment HL.
         Same as: LD (HL),A - INC HL
    """
    self.mmu.write(self.cpu.HL(), self.cpu.A)
    self.cpu.set_HL(self.cpu.HL() + 1 & 0xFFFF)


def LDI_A_HL(self):
    """
    15. LDI A,(HL)
        Description:
        Put value at address HL into A. Increment HL.
         Same as: LD A,(HL) - INC HL
    """
    self.cpu.A = self.mmu.read(self.cpu.HL())
    self.cpu.set_HL(self.cpu.HL() + 1 & 0xFFFF)


def LDD_HL_A(self):
    """
    12. LDD (HL),A
        Description:
         Put A into memory address HL. Decrement HL.
         Same as: LD (HL),A - DEC HL
    """
    self.mmu.write(self.cpu.HL(), self.cpu.A)
    self.cpu.set_HL(self.cpu.HL() - 1 & 0xFFFF)


def LDD_A_HL(self):
    """
    9. LDD A,(HL)
        Description:
         Put value at address HL into A. Decrement HL.
         Same as: LD A,(HL) - DEC HL
    """
    self.cpu.A = self.mmu.read(self.cpu.HL())
    self.cpu.set_HL(self.cpu.HL() - 1 & 0xFFFF)


def LDH_A_n(self, addr):
    """
    20. LDH A,(n)
        Description:
         Put memory address $FF00+n into A.
        Use with:
         n = one byte immediate value.
    """
    self.cpu.A = self.mmu.read(0xFF00 + addr)


def LDH_n_A(self, addr):
    """
    19. LDH (n),A
        Description:
         Put A into memory address $FF00+n.
        Use with:
         n = one byte immediate value.
    """
    self.mmu.write(0xFF00 + addr, self.cpu.A)


def LD_A_C(self):
    """
    5. LD A,(C)
        Description:
         Put value at address $FF00 + register C into A.
         Same as: LD A,($FF00+C)
    """
    self.cpu.A = self.mmu.read(0xFF00 + self.cpu.C)


def LD_C_A(self):
    """
    6. LD (C),A
        Description:
         Put A into address $FF00 + register C.
    """
    self.mmu.write(0xFF00 + self.cpu.C, self.cpu.A)


def LD_a16_SP(self, addr):
    """
    5. LD (nn),SP
        Description:
         Put Stack Pointer (SP) at address n.
        Use with:
         nn = two byte immediate address.
    """
    self.mmu.write(addr, self.cpu.SP & 0xFF)
    self.mmu.write(addr + 1, self.cpu.SP >> 8)


def LD_a16_A(self, value):
    """
    4. LD n,A
        Description:
         Put value A into n.
        Use with:
         nn = two byte immediate value. (LS byte first.)
    """
    self.mmu.write(value, self.cpu.A)


def LD_A_a16(self, value):
    """
    3. LD A,n
        Description:
         Put value n into A.
        Use with:
         nn = two byte immediate value. (LS byte first.)
    """
    self.cpu.A = self.mmu.read(value)


def LD_HL_SP_r8(self, value):
    """
    4. LDHL SP,n
        Description:
         Put SP + n effective address into HL.
        Use with:
         n = one byte signed immediate value.
        Flags affected:
         Z - Reset.
         N - Reset.
         H - Set or reset according to operation.
         C - Set or reset according to operation.
    """
    value = sign(value)
    res = self.cpu.SP + value

    self.cpu.set_flag_Z(False)
    self.cpu.set_flag_N(False)
    self.cpu.set_flag_H((self.cpu.SP & 0xF) + (value & 0xF) > 0xF)
    self.cpu.set_flag_C((self.cpu.SP & 0xFF) + (value & 0xFF) > 0xFF)
    self.cpu.set_HL(res & 0xFFFF)


def LD_SP_HL(self):
    """
    2. LD SP,HL
        Description:
         Put HL into Stack Pointer (SP).
    """
    self.cpu.SP = self.cpu.HL()


def DI(self):
    """
    9. DI
        Description:
         This instruction disables interrupts but not
         immediately. Interrupts are disabled after
         instruction after DI is executed.
        Flags affected:
         None.
    """
    self.cpu.ime = False


def EI(self):
    """
    10. EI
        Description:
         Enable interrupts. This intruction enables interrupts
         but not immediately. Interrupts are enabled after
         instruction after EI is executed.
        Flags affected:
         None.
    """
    self.cpu.ime = True
