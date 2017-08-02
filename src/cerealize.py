"""

    cerealize.py

"""

import attr
from typing import Tuple, Any
from enum import Enum
from abc import ABC, abstractmethod
from struct import pack, unpack
from functools import reduce
from struct import error as StructError

serializable = attr.s
validators = attr.validators
instance_of = validators.instance_of


# Following attrs, manually implement isclass to prevent importing inspect module
def isclass(clazz):
    return isinstance(clazz, type)


class Endian(Enum):
    LITTLE = "<"
    BIG = ">"


class Serializable(ABC):
    """
    Abstract class that serves as the parent of all serializable types
    """
    __attrs_attrs__ = None

    def __init__(self):
        pass


class SerialClass(Serializable):
    """
    Optional dummy parent class for use with custom classes using @serializable decorator
    Used to take advantage of IDE type-checking
    """
    pass


class SerialType(Serializable):
    """
    Abstract class which defines interface for all objects serving as serializable types
    """

    @abstractmethod
    def encode(self, value) -> bytes:
        """
        Encode a given value as the current type, which is defined by the overriding class

        :param value: Value to be encoded
        :return: Encoded bytes representing value as defined by the type
        """
        pass

    @abstractmethod
    def decode(self, buf: bytes) -> Tuple[any, bytes]:
        """
        Decode a byte stream into the current type

        :param buf: Byte stream to decode
        :return: Tuple of [value, bytes], where second element in tuple is either empty or contains any remaining bytes
                 not consumed by the decode operation
        """
        pass


class FixedSizeType(Serializable):
    """
    A special form of Serializable entity which has a fixed encoding length (number of bytes in encoded form)
    """
    @abstractmethod
    def get_size(self) -> int:
        """
        :return: Number of bytes occupied by the encoding of this type
        """
        pass


class FixedSizeClass(FixedSizeType):
    """
    Special form of FixedSizeType used for user-defined classes implementing @serializable decorator

    Classes should only extend FixedSizeClass if all of their serializable fields are in turn of type FixedSizeType
    """
    @classmethod
    def get_size(cls) -> int:
        """
        :return: Cumulative encoding size in bytes, defined as the sum of the sizes of the class's serializable fields
        """
        return sum([a.metadata['serial_type'].get_size() for a in cls.__attrs_attrs__])


class PrimitiveType(SerialType, FixedSizeType):
    """
    Defines a generic serializable primitive type
    """
    def __init__(self, size: int, symbol: str, byte_order: Endian=Endian.LITTLE):
        super().__init__()
        self.size = size
        self.fmt = byte_order.value + symbol

    def encode(self, value) -> bytes:
        return pack(self.fmt, value)

    def decode(self, buf: bytes) -> Tuple[any, bytes]:
        return unpack(self.fmt, buf[:self.size])[0], buf[self.size:]

    def get_size(self):
        return self.size


class Boolean(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=1, symbol='?', byte_order=byte_order)


class Uint8(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=1, symbol='B', byte_order=byte_order)


class Int8(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=1, symbol='b', byte_order=byte_order)


class Char(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=1, symbol='c', byte_order=byte_order)


class Int16(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=2, symbol='h', byte_order=byte_order)


class Uint16(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=2, symbol='H', byte_order=byte_order)


class Int32(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=4, symbol='i', byte_order=byte_order)


class Uint32(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=4, symbol='I', byte_order=byte_order)


class Int64(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=8, symbol='q', byte_order=byte_order)


class Uint64(PrimitiveType):
    def __init__(self, byte_order: Endian=Endian.LITTLE):
        super().__init__(size=8, symbol='Q', byte_order=byte_order)

bool_t = Boolean()
uint8_t = Uint8()
int8_t = Int8()
char_t = Char()
int16_t = Int16()
uint16_t = Uint16()
int32_t = Int32()
uint32_t = Uint32()
int64_t = Int64()
uint64_t = Uint64()


class StringType(SerialType, FixedSizeType):
    """
    Serializable type for handling standard Python strings
    """
    def __init__(self, size: int, encoding: str='utf8'):
        super().__init__()
        self.encoding = encoding
        self.size = size

    @classmethod
    def fmt(cls, size): return '%ds' % size

    def encode(self, value: str) -> bytes:
        return pack(StringType.fmt(self.size), bytes(value, self.encoding))

    def decode(self, buf: bytes) -> Tuple[str, bytes]:
        rawbytes = unpack(StringType.fmt(self.size), buf[:self.size])[0]
        dec = rawbytes.decode(self.encoding).rstrip('\0')
        return dec, buf[self.size:]

    def get_size(self):
        return self.size


def char_arr(x: int): return StringType(size=x)


class Array(SerialType, FixedSizeType):
    """
    Serializable type for encoding fixed-size arrays of values

    Values in the array must also be serializable as a FixedSizeType
    """
    def __init__(self, serial_type: FixedSizeType, length: int):
        super().__init__()
        self.t = serial_type
        self._length = length
        self._size = length * serial_type.get_size()

    def decode(self, buf: bytes) -> Tuple[list, bytes]:
        arr = []
        for i in range(0, self._length):
            val, buf = _decode_val(self.t, buf)
            arr.append(val)
        return arr, buf

    def encode(self, values: list) -> bytes:
        if len(values) > self._length:
            raise Exception("Sequence too long to encode.  Length = %d, required length = %d"
                            % len(values), self._length)
        chunks = []
        for i in range(0, self._length):
            if i < len(values):
                v = self._encode_element(values[i], i)
            else:
                v = bytes(self.t.get_size())
            chunks.append(v)
        return reduce(lambda x, y: x+y, chunks)

    def _encode_element(self, value, pos: int) -> bytes:
        try:
            return _encode_val(self.t, value)
        except Exception as e:
            raise Exception("Could not encode array value at position %d as SerialType %s. Python type = %s, value = %s"
                            % (pos, self.t.__class__.__name__, type(value), value)) from e

    def _empty_bytes(self):
        return bytes(self.t.get_size())

    def get_size(self):
        return self._size


def _supports_encoding(obj):
    return hasattr(obj, '__attrs_attrs__')


def _encode_val(kind: Serializable, value) -> bytes:
    if isinstance(kind, SerialType):
        return kind.encode(value)
    elif isclass(kind) and _supports_encoding(kind):
        return encode(value)
    raise Exception("Cannot encode value as serial type %s because it is neither a primitive type nor a serializable \
                     class" % kind)


def _encode_attr(attribute, obj) -> bytes:
    kind = attribute.metadata['serial_type']
    val = getattr(obj, attribute.name)
    if kind is None:
        return None

    try:
        return _encode_val(kind, val)
    except StructError as e:
        raise Exception("Could not encode field '%s' of '%s." % (attribute.name, obj.__class__)) from e
    except Exception as e:
        raise Exception("Error encoding field '%s'" % attribute.name) from e


def _decode_val(kind: Serializable, buf: bytes) -> Tuple[Any, bytes]:
    if isinstance(kind, SerialType):
        return kind.decode(buf)
    elif isclass(kind) and _supports_encoding(kind):
        return decode(kind, buf)
    raise Exception("Can't decode: Type %s is neither a primitive SerialType nor a SerialClass" % kind)


def _decode_attr(buf: bytes, attribute, cls) -> Tuple[Any, bytes]:
    kind = attribute.metadata['serial_type']
    if kind is None:
        return None
    try:
        return _decode_val(kind, buf)
    except Exception as e:
        raise Exception("Could not decode buffer into field '%s[%s]' of '%s."
                        % (attribute.name, kind.__class__.__name__, cls)) from e


def encode(obj: Serializable) -> bytes:
    """
    Encode a Serializable object into a byte stream

    :param obj: A serializable object
    :return: Byte stream representing the encoding of the object according to its serialization configuration
    """
    if not _supports_encoding(obj):
        raise Exception('Object does not support encoding')
    chunks = []
    for a in obj.__attrs_attrs__:
        c = _encode_attr(a, obj)
        if c is not None :
            chunks.append(c)
    return reduce(lambda x, y: x+y, chunks)


def decode(cls: Serializable, buf) -> Tuple[Any, bytes]:
    """
    Decode a bytestream as
    :param cls:
    :param buf:
    :return:
    """
    if not _supports_encoding(cls):
        raise Exception('Class does not support decoding')

    arg_list = {}

    for a in cls.__attrs_attrs__:
        val, buf = _decode_attr(buf, a, cls)
        arg_list[a.name] = val

    return cls(**arg_list), buf


def field(serial_type: Serializable=None, default=attr.NOTHING, validator=None, repr=True,
          cmp=True, hash=None, init=True, convert=None):
    metadata = {'serial_type': serial_type}
    return attr.ib(default, validator, repr, cmp, hash, init, convert, metadata)
