"""

Tests for built-in primitive types

"""

import unittest
import struct
from src.cerealize import *


class TestPrimitiveTypes(unittest.TestCase):
    def test_bool(self):
        self.assertEqual(b'\x00', bool_t.encode(False))
        self.assertEqual(b'\x01', bool_t.encode(True))

    def test_string(self):
        t = char_arr(6)
        self.assertEqual(b'hello!', t.encode("hello!"))
        self.assertEqual(t.decode(t.encode("hello!"))[0], "hello!")

    def test_uint8(self):
        self.assertEqual(b'\x00', uint8_t.encode(0))
        self.assertEqual(b'\t', uint8_t.encode(9))
        self.assertEqual(b'\xff', uint8_t.encode(255))

    def test_int_ranges(self):

        uint8_t.encode(255)
        with self.assertRaises(struct.error):
            uint8_t.encode(256)

        int8_t.encode(127)
        with self.assertRaises(struct.error):
            int8_t.encode(128)

        uint16_t.encode(65535)
        with self.assertRaises(struct.error):
            uint16_t.encode(65536)

        int16_t.encode(32767)
        with self.assertRaises(struct.error):
            int16_t.encode(32768)

        uint32_t.encode((2 ** 32) - 1)
        with self.assertRaises(struct.error):
            uint32_t.encode(2 ** 32)

        int32_t.encode(int(((2 ** 32) / 2)) - 1)
        with self.assertRaises(struct.error):
            int32_t.encode(int((2 ** 32) / 2))

        uint64_t.encode((2 ** 64) - 1)
        with self.assertRaises(struct.error):
            uint64_t.encode(2 ** 64)

        int64_t.encode(int(((2 ** 64) / 2)) - 1)
        with self.assertRaises(struct.error):
            int64_t.encode(int((2 ** 64) / 2))

        with self.assertRaises(struct.error):
            uint8_t.encode(-1)

        with self.assertRaises(struct.error):
            uint16_t.encode(-1)

        with self.assertRaises(struct.error):
            uint32_t.encode(-1)

        with self.assertRaises(struct.error):
            uint64_t.encode(-1)

    def test_uint8_array(self):
        t = Array(serial_type=uint8_t, length=10)
        self.assertEqual(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', t.encode([]))
        self.assertEqual(b'\x01\x05\xffC\x00\x00\x00\x00\x00\x00', t.encode([1, 5, 255, 67]))
        self.assertEqual(b'\x01\x05\xffC\x04\x01\x08\td\x9c', t.encode([1, 5, 255, 67, 4, 1, 8, 9, 100, 156]))

        t2 = Array(serial_type=uint8_t, length=3)
        input = [1, 5, 255]
        output, buf = t2.decode(t2.encode([1, 5, 255]))
        self.assertEqual(input, output)

        with self.assertRaises(Exception):
            t2.encode([1, 2, 3, 4]) # Input too long

if __name__ == '__main__':
    unittest.main()