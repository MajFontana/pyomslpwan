import bitstring
import numpy
import contextlib
from typing import Self



class Value:

    def getBitstream(self) -> numpy.ndarray:
        raise NotImplementedError
    
    def setBitstream(self, bitstream: numpy.ndarray):
        raise NotImplementedError



class Container(Value):
    
    def getSize(self) -> int:
        raise NotImplementedError

    def getData(self) -> numpy.ndarray:
        raise NotImplementedError
    
    def setData(self, data: numpy.ndarray):
        raise NotImplementedError
    
    def copyFrom(self, container: Self):
        self.setData(container.getData())
    
    def getBitstream(self) -> numpy.ndarray:
        data = numpy.nan_to_num(self.getData(), nan=-1)
        return (data > 0).astype(int)
    
    def setBitstream(self, bitstream: numpy.ndarray):
        self.setData(bitstream * 2 - 1)
    
    def getNrzStream(self) -> numpy.ndarray:
        data = numpy.nan_to_num(self.getData(), nan=0)
        return data
    
    def setNrzStream(self, nrz: numpy.ndarray):
        self.setData(nrz)
    
    def getBits(self):
        bitstream = self.getBitstream()
        return bitstring.Bits(bitstream.astype(numpy.bool_))
    
    def setBits(self, bits=None, **kwargs):
        if bits is None:
            size = self.getSize()
            if size > 0:
                bits = bitstring.Bits(length=size, **kwargs)
        self.setBitstream(numpy.array(bits))



class Field(Container):

    def __init__(self, size=0, bits=None, **kwargs):
        self.setSize(size)
        if (len(kwargs) > 0) or (bits is not None):
            self.setBits(bits, **kwargs)
    
    def getSize(self):
        return self.size
    
    def setSize(self, size):
        self.size = size
        self.data = numpy.full(self.size, numpy.nan)
    
    def getData(self):
        return self.data
    
    def setData(self, data):
        self.data[:] = data



class FieldGroup(Container):

    def __init__(self, fields: list[Container]):
        self.fields: list[Container] = fields
    
    def getSize(self):
        sizes = [field.getSize() for field in self.fields]
        return sum(sizes)
    
    def getData(self):
        data = [field.getData() for field in self.fields]
        return numpy.concatenate(data)
    
    def setData(self, data):
        pos = 0
        for field in self.fields:
            size = field.getSize()
            field.setData(data[pos:pos + size])
            pos += size
    
    def getPosition(self, target_field):
        pos = 0
        for field in self.fields:
            if field is target_field:
                return pos
            else:
                pos += field.getSize()
    
    def __setattr__(self, name, value):
            if hasattr(self, "_define_fields") and not name.startswith("__"):
                self.fields.append(value)
            super().__setattr__(name, value)
    
    @contextlib.contextmanager
    def defineFields(self):
        self.fields = []
        self._define_fields = True

        yield

        del self._define_fields