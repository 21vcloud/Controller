"File-based cache backend"
import errno
import glob
import io
import json
import os
import tempfile
import zlib

from .basecache import BaseCache

try:
    import cPickle as pickle
except:
    import pickle


class FileBasedCache(BaseCache):
    cache_suffix = '.cfg.cache'

    def __init__(self, dir):
        super(FileBasedCache, self).__init__()
        self._dir = os.path.abspath(dir)
        self._createdir()

    def refresh(self, namespace, value):
        self._createdir()  # Cache dir can be deleted at any time.

        fname = self._ns_to_file(namespace)
        fd, tmp_path = tempfile.mkstemp(dir=self._dir)
        renamed = False
        try:
            with io.open(fd, 'wb') as f:
                f.write(zlib.compress(pickle.dumps(value), -1))
            os.rename(tmp_path, fname)
            renamed = True
        finally:
            if not renamed:
                os.remove(tmp_path)

    def load(self, namespace, default=None):
        fname = self._ns_to_file(namespace)
        if os.path.exists(fname):
            try:
                with io.open(fname, 'rb') as f:
                    return pickle.loads(zlib.decompress(f.read()))
            except IOError as e:
                if e.errno == errno.ENOENT:
                    pass  # Cache file was removed after the exists check

        return default

    def delete(self, namespace):
        return self._delete(self._ns_to_file(namespace))

    def _delete(self, fname):
        if not fname.startswith(self._dir) or not os.path.exists(fname):
            return

        try:
            os.remove(fname)
        except OSError as e:
            # ENOENT can happen if the cache file is removed (by another
            # process) after the os.path.exists check.
            if e.errno != errno.ENOENT:
                raise

    def exists(self, namespace):
        fname = self._ns_to_file(namespace)
        if os.path.exists(fname):
            return True

        return False

    def _createdir(self):
        if not os.path.exists(self._dir):
            try:
                os.makedirs(self._dir, 0o700)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise EnvironmentError("Cache directory '%s' does not exist and could not be created'" % self._dir)

    def _ns_to_file(self, namespace):
        """
        Convert a key into a cache file path. Basically this is the
        root cache path joined with the md5sum of the namespace and a suffix.
        """
        return os.path.join(self._dir, ''.join([namespace, self.cache_suffix]))

    def clear(self):
        """
        Remove all the cache files.
        """
        if not os.path.exists(self._dir):
            return

        for fname in self._list_cache_files():
            self._delete(fname)

    def _list_cache_files(self):
        """
        Get a list of paths to all the cache files. These are all the files
        in the root cache dir that end on the cache_suffix.
        """
        if not os.path.exists(self._dir):
            return []

        return [os.path.join(self._dir, fname) for fname in glob.glob1(self._dir, '*%s' % self.cache_suffix)]


if __name__ == '__main__':
    data = json.loads(
        '{"a":1,"cluster": "default", "namespaceName": "application", "releaseKey": "20180724164952-d3ee4cedfd6bde9e", "configurations": {"test1": "aaaa", "switch": "123"}, "appId": "1001"}'
    )

    cache = FileBasedCache(dir="/home/vagrant/test/cache")

    cache.refresh("ns1", data)

    val = cache.load("ns1")

    print(val, type(val))
