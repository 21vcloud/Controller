import abc

from six import with_metaclass


class BaseCache(with_metaclass(abc.ABCMeta, object)):

    def __init__(self):
        pass

    def refresh(self, namespace, value):
        raise NotImplementedError('')

    def exists(self, namespace):
        raise NotImplementedError('')

    def load(self, namespace, default=None):
        raise NotImplementedError('')

    def delete(self, namespace):
        raise NotImplementedError('')

    def clear(self):
        raise NotImplementedError('')
