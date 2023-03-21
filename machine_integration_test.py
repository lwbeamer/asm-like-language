# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=no-self-use
# pylint: disable=line-too-long

"""Интеграционные тесты транслятора и машины
"""

import unittest

import machine
import translator


def start(source_code, output_file, input_file):
    translator.main([source_code, output_file])
    if input_file == "":
        return machine.main([output_file])
    return machine.main([output_file, input_file])


class TestMachine(unittest.TestCase):

    def test_hello(self):
        output = start("examples/hello.asm", "examples/hello_code.out", "")
        assert output == "Hello world!\0"

    def test_cat(self):
        output = start("examples/cat.asm", "examples/cat_code.out", "examples/input.txt")
        assert output == "Good news, everyone!"

    def test_prob5(self):
        output = start("examples/prob5.asm", "examples/prob5_code.out", "")
        print(output)
        assert output == '232792560'

    def test_sum(self):
        output = start("examples/sum.asm", "examples/sum_code.out", "")
        print(output)
        assert output == '5050'
