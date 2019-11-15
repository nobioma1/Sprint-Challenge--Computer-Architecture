"""CPU functionality."""

import sys

LDI = 0b10000010
PRN = 0b01000111
HLT = 0b00000001
MUL = 0b10100010
PUSH = 0b01000101
POP = 0b01000110
ADD = 0b10100000
CALL = 0b01010000
RET = 0b00010001
CMP = 0b10100111
JMP = 0b01010100


class CPU:
    """Main CPU class."""

    def __init__(self):
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0  # Program Counter
        self.sp = 7
        self.reg[self.sp] = 0xF4
        # setup branch table
        self.branch_table = {}
        self.branch_table[LDI] = self.handle_LDI
        self.branch_table[PRN] = self.handle_PRN
        self.branch_table[HLT] = self.handle_HLT
        self.branch_table[MUL] = self.handle_MUL
        self.branch_table[PUSH] = self.handle_PUSH
        self.branch_table[POP] = self.handle_POP
        self.branch_table[ADD] = self.handle_ADD
        self.branch_table[CALL] = self.handle_CALL
        self.branch_table[RET] = self.handle_RET
        self.branch_table[CMP] = self.handle_CMP
        self.branch_table[JMP] = self.handle_JMP
        self.running = False
        self.sub_pc = False
        self.fl = 0b000  # 000000LGE lower, greater, equal

    def load(self):
        """Load a program into memory."""
        address = 0

        if len(sys.argv) != 2:
            print("usage: ls8.py <filename>")
            sys.exit(1)

        try:
            with open(sys.argv[1]) as f:
                for line in f:
                    # deal with comments
                    # split before and after any comment symbol '#'
                    comment_split = line.split("#")

                    # convert the pre-comment portion (to the left) from binary to a value
                    # extract the first part of the split to a number variable
                    # and trim whitespace
                    num = comment_split[0].strip()

                    # ignore blank lines / comment only lines
                    if len(num) == 0:
                        continue

                    # set the number to an integer of base 2
                    instruction = int(num, 2)
                    self.ram[address] = instruction
                    address += 1

        except FileNotFoundError:
            print(f"{sys.argv[0]}: {sys.argv[1]} not found")
            sys.exit(2)

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == "ADD":
            # Add the value in reg a, b and store the result in reg_a
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "MUL":
            # Multiply the value in reg a, b and store the result in reg_a
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "CMP":
            # Compare the values in reg a, b
            # if value at reg_a == value at reg_b
            if self.reg[reg_a] == self.reg[reg_b]:
                # Set E flag to 1
                self.fl = 0b001
            # if value at reg_a < value at reg_b
            elif self.reg[reg_a] < self.reg[reg_b]:
                # Set L flag to 1
                self.fl = 0b100
            # if value at reg_a > value at reg_b
            elif self.reg[reg_a] > self.reg[reg_b]:
                # set G flag to 1
                self.fl = 0b010
            # otherwise
        else:
                # set flag to 0's
                self.fl = 0b000
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        # set to true to begin program run
        self.running = True
        while self.running:
            # Instruction at program counter
            IR = self.ram[self.pc]

            # put operands a and b in dict to pass to function
            operands = {
                "a": self.ram_read(self.pc + 1),
                "b": self.ram_read(self.pc + 2)
            }

            try:
                # Instruction to execute and pass operands to function
                self.branch_table[IR](operands)
            except KeyError:
                print(f"Unknown Instruction {IR:08b}")
                sys.exit(1)

            # Get the instruction size from IR
            # Right Shift by 6 and mask
            instruction_size = ((IR >> 6) & 0b11) + 1

            # If a sub-routine was not run
            if not self.sub_pc:
                # update the instruction size
                self.pc += instruction_size

    # Read a value in memory at a particular address
    def ram_read(self, MAR):
        # return the memory[Memory Address Register]
        return self.ram[MAR]

    # Write a value to the register at a particular address
    def raw_write(self, MAR, MDR):
        # Register[Memory Address Register] = Memory Data Register
        self.reg[MAR] = MDR

    def handle_LDI(self, operands):
        # Invoke the raw_write method to write to register at given address
        self.raw_write(operands["a"], operands["b"])
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    def handle_PRN(self, operands):
        # Print the value in the register at a given address
        print(self.reg[operands["a"]])
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    def handle_MUL(self, operands):
        # Invoke the ALU to perform MUL operation passing operands a and b
        self.alu("MUL", operands["a"], operands["b"])
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    def handle_PUSH(self, operands):
        # decrement self.sp
        self.reg[self.sp] -= 1
        # value at given register
        value = self.reg[operands["a"]]
        # address the stack pointer is pointing to
        address = self.reg[self.sp]
        # Push the value in the given register on the stack
        self.ram[address] = value
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    def handle_POP(self, operands):
        # Pop the value at the top of the stack into the given register
        self.reg[operands["a"]] = self.ram_read(self.reg[self.sp])
        self.reg[self.sp] += 1
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    # Calls a subroutine (function) at the address stored in the register
    def handle_CALL(self, operands):
        self.reg[self.sp] -= 1  # Decrement Stack Pointer
        # Push return location to stack
        self.ram[self.reg[self.sp]] = self.pc + 2
        # set pc to subroutine
        self.pc = self.reg[operands["a"]]
        # sub-routine operation, set sub_pc to True
        self.sub_pc = True

    def handle_RET(self, operands):
        # Return from subroutine
        # Pop the value from the top of the stack and store it in the `PC`
        self.pc = self.ram_read(self.reg[self.sp])
        self.reg[self.sp] += 1
        # sub-routine operation, set sub_pc to True
        self.sub_pc = True

    def handle_ADD(self, operands):
        # Invoke the ALU to perform ADD operation passing operands a and b
        self.alu("ADD", operands["a"], operands["b"])
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    def handle_CMP(self, operands):
        # Invoke the ALU to perform CMP operation passing operands a and b
        self.alu("CMP", operands["a"], operands["b"])
        # Not a sub-routine operation, set sub_pc to False
        self.sub_pc = False

    def handle_JMP(self, operands):
        # Jump to the address stored in the given register
        # Set the `PC` to the address stored in the given register.
        self.pc = self.reg[operands["a"]]
        # sub-routine operation, set sub_pc to True
        self.sub_pc = True

    def handle_HLT(self, operands):
        # set running to False to Halt/End program run
        self.running = False
