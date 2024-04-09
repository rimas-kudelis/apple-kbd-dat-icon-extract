class BaseRecognizer(object):
    header = b'start'
    footer = b'end'
    name = None

    recognizers = []

    @classmethod
    def is_data_start(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def find_next_data_start(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def find_data_size(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def find_data_range(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def find_next_data_range(cls, buf, pos):
        raise NotImplemented