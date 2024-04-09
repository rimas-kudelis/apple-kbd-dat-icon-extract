from .base import BaseRecognizer


class LanguageRecognizer(BaseRecognizer):
    header = None
    footer = None
    name = 'LANG'

    @classmethod
    def is_data_start(cls, buf, pos):
        return ((buf[pos]>96 and buf[pos]<123) or (buf[pos]>64 and buf[pos]<91) or (buf[pos]>47 and buf[pos]<58))

    @classmethod
    def find_next_data_start(cls, buf, pos):
        if pos >= len(buf):
            return None
        while buf[pos] == b'\x00':
            pos += 1
            if pos >= len(buf):
                return None
        if not cls.is_data_start(buf, pos):
            return None
        return pos

    @classmethod
    def read_cstring(cls, buf, pos):
        origin = pos
        pos = buf.find(b'\x00', origin)
        if pos == -1:
            return None
        return buf[origin:pos]

    @classmethod
    def read_data(cls, buf, pos):
        origin = pos
        assert cls.is_data_start(buf, origin)

        result = {'origin': origin}

        name = cls.read_cstring(buf, origin)
        if name is None:
            return None
        result['name'] = name
        result['size'] = size = len(name) + 1
        pos += size
        if pos >= len(buf):
            return result

        pos = cls.find_next_data_start(buf, pos)
        if pos is None:
            return result
        code = cls.read_cstring(buf, pos)
        if code is None:
            return result

        pos += len(code) + 1

        result['code'] = code
        result['size'] = pos - origin

        return result

    @classmethod
    def find_data_size(cls, buf, pos):
        assert cls.is_data_start(buf, pos)
        origin = pos
        pos = buf.find(b'\x00', pos)
        if pos == -1:
            return None
        pos = cls.find_next_data_start(buf, pos)
        if pos is None:
            return None
        pos = buf.find(b'\x00', pos)
        if pos == -1:
            return None
        pos += 1
        if pos >= len(buf):
            return None
        return pos - origin

    @classmethod
    def find_data_range(cls, buf, pos):
        origin = pos
        size = cls.find_data_size(buf, pos)
        if size is None:
            return None
        return (origin, size)

    @classmethod
    def find_next_data_range(cls, buf, pos):
        pos = cls.find_next_data_start(buf, pos)
        if pos is None:
            return None
        r = cls.find_data_range(buf, pos)
        if r is None:
            return None
        return r

    @classmethod
    def read_next_data(cls, buf, pos):
        pos = cls.find_next_data_start(buf, pos)
        if pos is None:
            return None
        return cls.read_data(buf, pos)
