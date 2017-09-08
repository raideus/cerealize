# cerealize 
**Declarative object serialization for Python**

cerealize is a library that allows you to define custom binary serialization functionality for Python objects using a declarative syntax.  It is built on top of attrs and is effectively a superset of that package.

The motiviation for creating this library was to reduce the amount of boilerplate code needed to implement message creation and parsing for networked / distributed software.  With cerealize you can use real classes for representing your packets and messages, and define the serialization of those messages directly within your class definitions.

### Built for OOP
Inspired by existing packages such as [construct](https://github.com/construct/construct), cerealize enables a similar declarative style of defining serialization behavior.  Where cerealize stands out however is in its optimization for object-oriented programming: You can use full-featured classes to represent your messages, complete with encapsulated data and logic, and also define the serialization behavior directly within the class definition.  

### Compatible with attrs
cerealize is a superset of the [attrs](https://github.com/python-attrs/attrs) package, and thus fully backward compatible (for Python 3.x).  
