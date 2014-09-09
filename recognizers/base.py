class BaseRecognizer(object):
    header = 'start'
    footer = 'end'
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