# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=no-self-use

"""Интеграционные тесты транслятора и машины
"""

import unittest

import isa
import translator


def start(input_file, output_file, correct_file):
    translator.main([input_file, output_file])
    result = isa.read_code(output_file)
    correct_code = isa.read_code(correct_file)
    assert result == correct_code


class TestTranslator(unittest.TestCase):

    def test_prob5(self):
        start("examples/prob5.asm", "examples/prob5_code.out",
              "examples/correct_prob5_code.out")

    def test_cat(self):
        start("examples/cat.asm", "examples/cat_code.out",
              "examples/correct_cat_code.out")

    def test_hello_world(self):
        start("examples/hello.asm", "examples/hello_code.out",
              "examples/correct_hello_code.out")

    def test_sum(self):
        start("examples/sum.asm", "examples/sum_code.out",
              "examples/correct_sum_code.out")
