from threading import RLock


class EmptyPlaylistException(Exception):
    def __init__(self):
        pass


class DemocraticPlaylist:
    def __init__(self, **config):

        super().__init__()

        if "DEFAULT_PLAYLIST_ID" not in config:
            raise RuntimeError("DEFAULT_PLAYLIST_ID is not defined")

        self.playlist_name = config.get('DEMOCRATIC_PLAYLIST_NAME', '')
        self.playlist_id = config.get('DEMOCRATIC_PLAYLIST_ID', '')
        self._lock = RLock()
        self._track_map = {}
        self._track_list = []
        self._current_track = None
        self._default_track_set = set()
        self._default_playlist_id = config['DEFAULT_PLAYLIST_ID']

    def _update_default_playlist(self):
        """ Updates the list of default tracks to be used in case the main playlist
            is empty. Implementation depends on the back-end used """

        raise NotImplementedError(
            '_update_default_playlist cannot be called in DefaultPlaylist')

    def vote(self, track_info):
        """ Add one vote to the track and update the internal data structures """

        # TODO rewrite this more nicely
        with self._lock:
            current_votes = 0
            track_id = track_info.id
            if track_id in self._track_map.keys():
                pos = self._track_map[track_id]
                current_votes, _ = self._track_list[pos]
                del self._track_list[pos]
            elif track_id in self._default_track_set:
                self._default_track_set.remove(track_id)
                self._track_list.insert(0, track_id)
                self._track_map = {k: v+1 for k, v in self._track_map.items()}
                self._track_map[track_id] = 0
                return

            current_votes += 1
            left = [x for x in self._track_list if x[0] < current_votes]
            right = [x for x in self._track_list if x[0] >= current_votes]

            self._track_list = left + [(current_votes, track_info)] + right
            self._track_map[track_id] = len(left)

            # Correct the positions of the tracks that swapped their position with the
            # track being currently voted
            for i in range(len(self._track_list)):
                _, track_info = self._track_list[i]
                self._track_map[track_info.id] = i

    def next(self):
        """ Get the next track. Resort to the default playlist in case the democratic
            playlist is empty """

        with self._lock:
            if not self._track_list:
                return self._next_from_default_playlist()

            _, self._current_track = self._track_list.pop()
            del self._track_map[self._current_track.id]
            return self._current_track

    def _next_from_default_playlist(self):
        """ Gets a track from the default playlist. Update it in case it's empty """

        if not self._default_track_set:
            self._update_default_playlist()
        self._current_track = self._default_track_set.pop()
        return self._current_track

    def current(self):
        """ Return the latest track that was popped from the playlist """

        return self._current_track

    def __len__(self):
        return len(self._track_list)

    def get_tracks(self):
        """ Returns [(votes, TrackInfo)] populated with the tracks from the democratic
            playlist. The list is reversed so that elements are ordered decreasingly
            according to the number of votes """
        with self._lock:
            return self._track_list[::-1]
