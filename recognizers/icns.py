import struct
from .base import BaseRecognizer


class ICNSRecognizer(BaseRecognizer):
    header = b'icns'
    footer = b'IEND\xaeB\x60\x82'
    name = 'ICNS'

    @classmethod
    def is_data_start(cls, buf, pos):
        return buf.startswith(cls.header, pos)

    @classmethod
    def find_next_data_start(cls, buf, pos):
        if pos >= len(buf):
            return None
        pos = buf.find(cls.header, pos)
        return pos if pos != -1 else None

    @classmethod
    def find_data_size(cls, buf, pos):
        origin = pos
        assert cls.is_data_start(buf, origin)
        pos += len(cls.header)
        size = struct.unpack('>I', buf[pos:pos+4])[0]
        #print "icns range: {} - {} (size: {})".format(*[origin, origin + size, size])
        assert origin + size < len(buf)
        # Usually, the icon ends with cls.footer, but not always.
        # Trust the offset we extracted instead.
        #assert buf[origin + size - len(cls.footer):origin + size] == cls.footer
        return size

    @classmethod
    def find_data_range(cls, buf, pos):
        size = cls.find_data_size(buf, pos)
        return (pos, size)

    @classmethod
    def find_next_data_range(cls, buf, pos):
        origin = cls.find_next_data_start(buf, pos)
        if origin is None:
            return None
        return cls.find_data_range(buf, origin)
