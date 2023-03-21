"""Типы данных для представления и сериализации/десериализации машинного кода."""
# !/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью

import json
from enum import Enum


class Opcode(str, Enum):
    """Opcode для ISA."""

    HLT = 'hlt'
    MOV = 'mov'
    CMP = 'cmp'
    CMP_REL_INC = 'cmp_rel_inc'
    RDIV = 'rdiv'
    ADD = 'add'
    INC = 'inc'

    IN = 'in'
    OUT = 'out'
    OUT_CHAR = 'out_char'
    OUT_REL = 'out_rel'
    JMP = 'jmp'
    JE = 'je'
    SV = 'sv'


inst_to_mc = {
    'hlt': [14],
    'mov': [0, 3, 12],
    'cmp': [0, 6, 12],
    'cmp_rel_inc': [0, 2, 6, 9, 5, 12],
    'rdiv': [0, 7, 12],
    'add': [0, 8, 3, 12],
    'in': [1, 12],
    'out': [0, 10, 12],
    'out_char': [0, 11, 12],
    'out_rel': [0, 2, 11, 12],
    'jmp': [13],
    'je': [15],
    'sv': [4, 12]
}


def write_code(filename, code, data):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))

    with open("data_file", "w", encoding="utf-8") as file:
        file.write(json.dumps(data, indent=4))


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    with open("data_file", encoding="utf-8") as file:
        data_section = json.loads(file.read())

    return code, data_section
