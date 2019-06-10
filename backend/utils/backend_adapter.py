""" This class is used by the backend to decorate the different methods that have
    to return sth to the front-end and perform the translation from whatever the backend
    returns (e.g. json) to whatever the front-end expects (e.g. sth of the type TrackInfo)
"""

from collections import namedtuple
from functools import wraps

TrackInfo = namedtuple('TrackInfo', ['name', 'artist', 'album', 'id', 'length'])
AlbumInfo = namedtuple('AlbumInfo', ['name', 'artist', 'id'])
ArtistInfo = namedtuple('ArtistInfo', ['name', 'id'])

class BackendAdapter:
    """ Contains an adapter registry and the decorator used to apply the adapter """

    def __init__(self):
        self.adapter_registry = {}

    def register(self, backend_function):
        """ Wraps the given function so the associated adapter (in case there's any)
            process its return value before it reaches the front-end """
        @wraps(backend_function)
        def adapted_method(*args, **kwargs):
            if backend_function.__name__ not in self.adapter_registry:
                return backend_function(*args, **kwargs)
            adapter = self.adapter_registry[backend_function.__name__]
            return adapter(backend_function(*args, **kwargs))
        return adapted_method
