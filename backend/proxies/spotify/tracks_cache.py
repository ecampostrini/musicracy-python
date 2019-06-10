""" Defines a cache for tracks info populated by 'search' and used by 'vote'. Defines an
    instance which is to be used as a singleton which is ugly but it's not meant as a
    general solution and can be considered an implementation specific (to the Spotify
    client) detail """

from functools import wraps

class TracksCache:
    """ Class to be used as a singleton. Provides caching of a list of tracks
        and support for retrieval of cached values """

    def __init__(self, limit=1000):
        self.max_size = limit
        self.track_id_list = []
        self.cache = {}

    def cache_results(self, function):
        """ Caches the results of the wrapped functions and returns them """

        @wraps(function)
        def wrapper(*args, **kwargs):
            track_info_list = function(*args, **kwargs)
            for track_info in track_info_list:
                if track_info.id in self.cache:
                    continue
                elif len(self.track_id_list) > self.max_size:
                    self.track_id_list.pop()
                self.cache[track_info.id] = track_info
                self.track_id_list.insert(0, track_info.id)
            return track_info_list

        return wrapper

    def __contains__(self, track_id):
        """ Checks if the track with ID track_id is in the cache """

        return track_id in self.cache

    def __getitem__(self, key):
        """ Provides [] operator to the class """

        return self.cache[key]

tracks_cache = TracksCache()
