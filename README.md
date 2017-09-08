# cerealize 
**Declarative object serialization for Python**

cerealize is a library that allows you to define custom binary serialization functionality for Python objects using a declarative syntax.  It is built on top of attrs and is effectively a superset of that package.

The motiviation for creating this library was to reduce the amount of boilerplate code needed to implement message creation and parsing for networked / distributed software.  With cerealize you can use real classes for representing your packets and messages, and define the serialization of those messages directly within your class definitions.

### Built for OOP
Inspired by existing packages such as [construct](https://github.com/construct/construct), cerealize enables a similar declarative style of defining serialization behavior.  Where cerealize stands out however is in its optimization for object-oriented programming: You can use full-featured classes to represent your messages, complete with encapsulated data and logic, and also define the serialization behavior directly within the class definition.  

### Compatible with attrs
cerealize is a superset of the [attrs](https://github.com/python-attrs/attrs) package, and thus fully backward compatible (for Python 3.x).  

### C-Like Type Definitions

Most network protocols rely on C data types to specify the form of message fields.  Cerealize provides C-Like type defintions to ease the process of implementing code from protocol documentation, such that the resulting classes resemble C structs.

Consider a hypothetical C struct for representing a packet header:
```c
struct Header {
  uint32_t version;
  char sender[12];
  bool flag;
  int64_t checksum;
};

```

The equivalent Python class implemented with cerealize would be:
```python
@serializable
class Header(SerialClass):
    version = field(serial_type=uint32_t)
    sender = field(serial_type=string_t(12))
    flag = field(serial_type=boolean)
    checksum = field(serial_type=int64_t)
```


### Example

Let's say we have a message type *Foo* that we want to represent as a class.  This message has 4 fields *w,x,y,z* with types int16_t\[5\], boolean, int32_t, and a string of at most 12 characters (char\[12\]).  We can declare this message as follows:

```python
import 

@serializable
class Foo:
    w = field(Array(int16_t, 5))
    x = field(bool_t)
    y = field(int32_t)
    z = field(string_t(12))
```

We can now instantiate messages as regular Python objects:
```python
>>> myObject = Foo(w=[1,2,5,6,7], x=True, y=938281, z="Hello world!")
>>> myObject

Foo(w=[1, 2, 5, 6, 7], x=True, y=938281, z='Hello world!')
```

To send our messages over the wire, we pass the message object to cerealize's **encode()** function to convert it to a stream of bytes:

```
>>> encodedBytes = encode(myObject)
>>> encodedBytes

b'\x00\x01\x00\x02\x00\x05\x00\x06\x00\x07\x01\x00\x0eQ)Hello world!'
```

On the receiving end, a buffer of bytes is passed to cerealize's **decode()** function (in addition to the target class) to convert bytes back into a live Python object:

```
>>> decodedObject, buf = decode(Foo, encodedBytes)
>>> decodedObject

Foo(w=[1, 2, 5, 6, 7], x=True, y=938281, z='Hello world!')
```
