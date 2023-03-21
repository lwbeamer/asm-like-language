"""Module machine. Realisation of model"""
# !/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=too-many-instance-attributes    # атрибуты нужны
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис
# pylint: disable=too-many-branches     # нет смысла сворачивать ифы в трудночитаемый код
# pylint: disable=too-many-statements#
# pylint: disable=no-self-use

import logging
import sys
from enum import Enum
from isa import Opcode, read_code, inst_to_mc


class AluLeftMuxSignals(Enum):
    """Сигналы для левого входа АЛУ."""
    MEM = 1
    BR = 2


class AluRightMuxSignals(Enum):
    """Сигналы для правого входа АЛУ."""
    ACC = 1
    ZERO = 2


class AccMuxSignals(Enum):
    """Сигналы для выбора значения, попадающего в аккумулятор."""
    ALU = 1
    MEM = 2
    INPUT = 3


class DataPath:
    """Тракт данных, включая: ввод/вывод, память и арифметику."""

    def __init__(self, data_memory_size, input_buffer, data_section):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.data_address = 0
        self.alu = 0
        self.acc = 0
        self.br = 0

        self.input_buffer = input_buffer
        self.output_buffer = []
        for var_addr, variable in enumerate(data_section):
            self.data_memory[var_addr] = int(variable)

    def latch_data_addr(self, addr):
        assert 0 <= int(addr) <= self.data_memory_size, \
            f'data_address must be in [0;{self.data_memory_size}]'
        self.data_address = int(addr)

    def latch_acc(self, sel):
        if sel == AccMuxSignals.MEM:
            self.acc = self.data_memory[self.data_address]
        elif sel == AccMuxSignals.ALU:
            self.acc = self.alu
        elif sel == AccMuxSignals.INPUT:
            if len(self.input_buffer) == 0:
                raise EOFError()
            symbol = self.input_buffer.pop(0)
            symbol_code = ord(symbol)
            assert 0 <= symbol_code <= 127, \
                "input character is out of bound: {}".format(symbol_code)
            self.acc = ord(symbol)

    def latch_br(self):
        self.br = self.alu

    def alu_sel_op(self, operation, sel_left, sel_right):
        left_value = self.data_memory[self.data_address] \
            if sel_left == AluLeftMuxSignals.MEM \
            else self.br
        right_value = self.acc if sel_right == AluRightMuxSignals.ACC else 0

        if operation == Opcode.CMP:
            self.alu = left_value - right_value

        if operation == Opcode.RDIV:
            self.alu = right_value % left_value

        if operation == Opcode.ADD:
            self.alu = left_value + right_value

        if operation == Opcode.INC:
            self.alu = left_value + 1

    def output(self, is_char):
        symbol = self.acc
        if is_char:
            symbol = chr(symbol)
        else:
            symbol = str(symbol)
        logging.debug('output: %s << %s', repr(
            ''.join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)

    def write(self, value):
        self.data_memory[self.data_address] = value

    def zero(self):
        return self.acc == 0


class ControlUnit:
    """Блок управления процессора."""

    def __init__(self, data_path, program):
        self.data_path = data_path
        self.program = program
        self._tick = 0
        self.program_counter = 0
        self.args = []

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def current_args(self):
        return self.args

    def decode_and_execute_instruction(self):
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        self.args = instr["args"]
        for mc in inst_to_mc[opcode]:
            self.mc_memory[mc](self)
            self.tick()
            logging.debug('%s', self)

    def read_first_arg(self):
        self.data_path.latch_data_addr(self.args[0])
        self.data_path.latch_acc(AccMuxSignals.MEM)

    def write_from_input(self):
        self.data_path.latch_acc(AccMuxSignals.INPUT)
        self.data_path.latch_data_addr(self.args[0])
        self.data_path.write(self.data_path.acc)

    def read_from_acc_addr(self):
        self.data_path.latch_data_addr(self.data_path.acc)
        self.data_path.latch_acc(AccMuxSignals.MEM)

    def write_acc_by_second_arg(self):
        self.data_path.latch_data_addr(self.args[1])
        self.data_path.write(self.data_path.acc)

    def write_acc_by_first_arg(self):
        self.data_path.latch_data_addr(self.args[0])
        self.data_path.write(self.data_path.acc)

    def write_br(self):
        self.data_path.latch_data_addr(self.args[0])
        self.data_path.write(self.data_path.br)

    def alu_cmp(self):
        self.data_path.latch_data_addr(self.args[1])
        self.data_path.alu_sel_op(Opcode.CMP, AluLeftMuxSignals.MEM, AluRightMuxSignals.ACC)
        self.data_path.latch_acc(AccMuxSignals.ALU)

    def alu_rdiv(self):
        self.data_path.latch_data_addr(self.args[1])
        self.data_path.alu_sel_op(Opcode.RDIV, AluLeftMuxSignals.MEM, AluRightMuxSignals.ACC)
        self.data_path.latch_acc(AccMuxSignals.ALU)

    def alu_add(self):
        self.data_path.latch_data_addr(self.args[1])
        self.data_path.alu_sel_op(Opcode.ADD, AluLeftMuxSignals.MEM, AluRightMuxSignals.ACC)
        self.data_path.latch_acc(AccMuxSignals.ALU)

    def inc_addr(self):
        self.data_path.latch_data_addr(self.args[0])
        self.data_path.alu_sel_op(Opcode.INC, AluLeftMuxSignals.MEM, AluRightMuxSignals.ZERO)
        self.data_path.latch_br()

    def out_num(self):
        self.data_path.output(is_char=False)

    def out_char(self):
        self.data_path.output(is_char=True)

    def next_instr(self):
        self.program_counter += 1

    def jump_instr(self):
        self.program_counter = self.args[0]

    def stop_program(self):
        raise StopIteration

    def jmp_zero(self):
        if self.data_path.zero():
            self.program_counter = self.args[0]
        else:
            self.program_counter += 1

    mc_memory = [read_first_arg, write_from_input, read_from_acc_addr, write_acc_by_second_arg,
                 write_acc_by_first_arg, write_br, alu_cmp, alu_rdiv,
                 alu_add, inc_addr, out_num, out_char,
                 next_instr, jump_instr, stop_program, jmp_zero]

    def __repr__(self):
        state = "{{TICK: {}, ADDR: {}, PC: {}, OUT: {}, ACC: {}}}".format(
            self._tick,
            self.data_path.data_address,
            self.program_counter,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.acc,
        )

        return "{} ".format(state)


def simulation(code, input_tokens, data_memory_size, limit, data_section):
    data_path = DataPath(data_memory_size, input_tokens, data_section)
    control_unit = ControlUnit(data_path, code)
    instr_counter = 0

    logging.debug('%s', control_unit)

    try:
        while True:
            assert limit > instr_counter, "too long execution, increase limit!"
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
    except EOFError:
        logging.warning('Input buffer is empty!')
    except StopIteration:
        pass
    logging.info('output_buffer: %s', repr(''.join(data_path.output_buffer)))
    return ''.join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(args):
    assert 1 <= len(args) <= 2, "Wrong arguments: machine.py <code_file> [ <input_file> ]"

    if len(args) == 2:
        code_file, input_file = args
    else:
        code_file = args[0]
        input_file = ''

    code, data_section = read_code(code_file)

    if input_file != '':
        with open(input_file, encoding="utf-8") as file:
            input_text = file.read()
            input_token = []
            for char in input_text:
                input_token.append(char)
    else:
        input_token = []

    output, instr_counter, ticks = simulation(code,
                                              input_tokens=input_token,
                                              data_memory_size=100, limit=1000000000,
                                              data_section=data_section)

    print(''.join(output))
    print("instr_counter:", instr_counter, "ticks:", ticks)
    return ''.join(output)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
