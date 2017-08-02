"""
Tests for custom serializable objects
"""

import unittest
from src.cerealize import *


class TestObjects(unittest.TestCase):
    def test_basic_object(self):
        @serializable
        class Foo:
            x = field(serial_type=uint16_t)
            y = field(serial_type=char_arr(5))

        f = Foo(x=16, y="hello")
        self.assertEqual(16, f.x)
        self.assertEqual("hello", f.y)

        encoded = encode(f)
        decoded, buf = decode(Foo, encoded)

        self.assertEqual(b'\x10\x00hello', encoded)
        self.assertEqual(decoded, f)

    def test_fixed_length_object(self):
        @serializable
        class Foo(SerialClass, FixedSizeClass):
            x = field(serial_type=uint16_t)
            y = field(serial_type=char_arr(5))
            z = field(serial_type=bool_t)

        self.assertEqual(8, Foo.get_size())

        f = Foo(x=781, y="hi", z=True)
        self.assertEqual(8, f.get_size())

        f = Foo(x=1, y="h", z=False)
        self.assertEqual(8, f.get_size())

    def test_object_array(self):
        @serializable
        class Foo(SerialClass, FixedSizeClass):
            x = field(serial_type=bool_t)
            y = field(serial_type=int32_t)

        self.assertEqual(5, Foo.get_size())

        t = Array(serial_type=Foo, length=3)
        self.assertEqual(5 * 3, t.get_size())

        v1 = Foo(True, 17)
        v2 = Foo(False, -123)
        v3 = Foo(True, 9999)

        input = [v1, v2, v3]
        self.assertEqual(b"\x01\x11\x00\x00\x00\x00\x85\xff\xff\xff\x01\x0f'\x00\x00", t.encode(input))
        self.assertEqual(t.decode(t.encode(input))[0], input)

if __name__ == '__main__':
    unittest.main()
