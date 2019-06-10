""" Class containing a high-level client of Spotify's API intended to be
    used by the player """

from urllib.parse import urlencode, quote
import threading
import time
import requests

from backend.utils.democratic_playlist import DemocraticPlaylist
from backend.utils.log import get_logger
from backend.utils.backend_adapter import TrackInfo
import backend.controller as Controller

from .adapter import backend_adapter
from .constants import API_URL, AUTH_TOKEN_FMT
from .tracks_cache import tracks_cache
from .utils import spotify_request, gen_playlist_name
from .connector import SpotifyConnector

logger = get_logger("backend")


class SpotifyClient(SpotifyConnector, DemocraticPlaylist):
    """ Derived class implementing the calls to the API. The splitting
        is done to avoid having a huge source file that contains both
        the details of authentication and token refresh along with the
        details of the 'high-level' calls to the API """

    def __init__(self, **config):
        """ Initializes the mixin classes and the logger. Will probably
            choose the Spotify device and start the playback in the future
        """

        if 'DEFAULT_PLAYLIST_ID' not in config:
            raise RuntimeError('Config missing: DEFAULT_PLAYLIST_ID')

        super().__init__(**config)

        # self._default_playlist_id = app.config.get('spotify_default_playlist_id, '')
        self.running = True
        self.state_checking_thread = None
        self.is_playing = threading.Event()

    def initialize(self, controller: Controller.Controller):
        """
            Idempotent function that: creates a new playlist in Spotify in case there's
            none, lauches a thread that polls the state of the Spotify player until
            is playing and then synchronizes the state of the Controller to match that.
            Returns `True` if initialization was properly performed and `False` otherwise.
            It is part of an ugly hack to (try to) overcome Spotify's API limitations
            described in https://github.com/spotify/web-api/issues/462
        """

        if self.is_playing.is_set():
            self.state_checking_thread.join(1.0)
            return {"is_playing": True}

        # Create and populate a playlist in Spotify and adjust the controller's internal state
        if not self.playlist_id:
            self.playlist_id = self.create_playlist(gen_playlist_name())['id']
            next_track = self.next()
            logger.debug("Will initialize playlist with track %s", next_track)
            self.add_track(next_track.id)
            controller._remaining_in_secs = next_track.length - 5
            controller._state = Controller.STATE_PAUSED

        if not self.state_checking_thread:
            def state_checker(client: SpotifyClient,
                              controller: Controller.Controller):
                """Function used by the thread that checks the state of the player"""
                while client.running:
                    player_info = client.get_player_info()
                    if player_info['is_playing']:
                        client.is_playing.set()
                        controller.queue.put(Controller.PLAY)
                        logger.debug(
                            "Spotify player is playing. Nothing else to do for the state "
                            "checking thread. Over and out !")
                        break

            # Launch the thread and give it some time to initialize
            self.state_checking_thread = threading.Thread(
                target=state_checker, args=(self, controller))
            self.state_checking_thread.start()
            time.sleep(2)

        return {"is_playing": False}

    def finish(self):
        """ Stop following the playlist at exit to avoid polluting the client's profile """

        self.running = False
        num_tries = 0
        while self.state_checking_thread and self.state_checking_thread.is_alive():
            if num_tries >= 5:
                logger.info(
                    "Couldn't join the state checking thread after 5 tries."
                    "Will leave anyway")
                break
            self.state_checking_thread.join(1.0)
            num_tries += 1

        self.unfollow_playlist()
        SpotifyConnector.finish(self)

    def _update_default_playlist(self):
        """ Override method from the DemocraticPlaylist """

        # This filter gets us all the information we need for our use case.
        # For more info check:
        # https://beta.developer.spotify.com/documentation/web-api/reference/playlists/get-playlists-tracks/
        query_filter = 'items(track(album, artists, duration_ms, name, id, uri))'
        default_playlist = self.get_playlist(
            self._default_playlist_id, fields=query_filter)["result"]

        self._default_track_set = set([
            TrackInfo(
                t["name"],
                t["artist"],
                t["album"],
                t["id"],
                t["length"])
            for t in default_playlist])
        # logger.debug("Default playlist: %s", self._default_track_set)

    # @tracks_cache.cache_results
    @backend_adapter.register
    @spotify_request
    def search(self, limit=1, item_type=None, **filters):
        """ Search for a specific item using the given filters.
            Supported items are: track, artist, album """

        if not filters:
            logger.debug('search called without filters. '
                         'Will return an empty object')
            return []

        if not item_type or item_type.lower() not in [
                'track', 'artist', 'album']:
            logger.debug('Invalid or empty item type given for the '
                         'search. Will use \'track\' as a default')
            item_type = 'track'
        else:
            item_type = item_type.lower()

        query_str = (' '.join([filter_name + ':' + filter_val for
                               filter_name, filter_val
                               in filters.items() if len(filter_val)]))

        logger.debug("Search called with query string:\n %s", query_str)

        payload = {}
        payload['q'] = query_str
        payload['type'] = item_type
        payload['limit'] = limit

        return requests.get(url=API_URL + 'search',
                            params=urlencode(payload, quote_via=quote),
                            headers={'Authorization':
                                     AUTH_TOKEN_FMT.format(self._access_token)})

    @spotify_request
    def play(self, **kwargs):
        """
        Send play to Spotify
        """

        return requests.put(url=API_URL + 'me/player/play',
                            json=kwargs if len(kwargs) else None,
                            headers={'Authorization':
                                     AUTH_TOKEN_FMT.format(self._access_token)})

    @spotify_request
    def pause(self):
        """
        Send pause to Spotify
        """

        return requests.put(url=API_URL + 'me/player/pause',
                            headers={'Authorization':
                                     AUTH_TOKEN_FMT.format(self._access_token)})

    @spotify_request
    def create_playlist(self, name, public=False, description=None):
        """ creates a playlist on behalf of the _user_id with the
        given name """

        endpoint = '{api_url}users/{user_id}/playlists'.format(
            api_url=API_URL,
            user_id=self.user_id)

        payload = {}
        payload['name'] = name
        payload['public'] = public
        if description:
            payload['description'] = description

        return requests.post(
            url=endpoint, json=payload,
            headers={'Authorization': AUTH_TOKEN_FMT.format(
                self._access_token)})

    @spotify_request
    def add_track(self, track_id):
        """ Add a track with the given uri to the given playlist """

        # New endpoint, already enabled by Spotify but old one not yet deprecated
        # endpoint = '{api_url}playlists/{playlist_id}/tracks'.format(
        #     api_url=API_URL,
        #     playlist_id=self.playlist_id)

        endpoint = '{api_url}users/{user_id}/playlists/{playlist_id}/tracks'.format(
            api_url=API_URL, user_id=self.user_id, playlist_id=self.playlist_id)

        payload = {}
        payload['uris'] = [track_id]  # XXX this does not handle multiple tracks

        return requests.post(
            url=endpoint, json=payload,
            headers={'Authorization': AUTH_TOKEN_FMT.format(
                self._access_token)})

    @backend_adapter.register
    @spotify_request
    def get_user_devices(self):
        """ Retrieve the list of devices on which Spotify is enabled """

        endpoint = '{api_url}me/player/devices'.format(api_url=API_URL)

        return requests.get(url=endpoint,
                            headers={'Authorization':
                                     AUTH_TOKEN_FMT.format(self._access_token)})

    @spotify_request
    def set_user_device(self, device_id):
        """ Set the given devices as the one to be used for Spotify playback """

        endpoint = '{api_url}me/player'.format(api_url=API_URL)
        payload = {'device_ids': [device_id]}

        return requests.put(url=endpoint,
                            json=payload,
                            headers={'Authorization':
                                     AUTH_TOKEN_FMT.format(self._access_token)})

    @spotify_request
    def unfollow_playlist(self):
        """ Unfollow the playlist so it doesn't appear amongst the user's
            playlists """

        endpoint = '{}playlists/{}/followers'.format(API_URL,
                                                     self.playlist_id)

        return requests.delete(
            url=endpoint,
            headers={'Authorization': AUTH_TOKEN_FMT.format(
                self._access_token)})

    @backend_adapter.register
    @spotify_request
    def get_playlist(self, playlist_id, fields, offset=0):
        """ Retrieves a list of tracks from a particular Spotify playlist """

        endpoint = '{api_url}playlists/{playlist_id}/tracks'.format(
            api_url=API_URL, playlist_id=playlist_id)

        payload = {}
        payload['fields'] = fields
        payload['offset'] = offset
        payload['market'] = 'from_token'

        return requests.get(url=endpoint,
                            params=urlencode(payload, quote_via=quote),
                            headers={'Authorization':
                                     AUTH_TOKEN_FMT.format(self._access_token)})

    @backend_adapter.register
    @spotify_request
    def get_track(self, track_id):
        """ Gets the track_info associated to the given track_id """

        endpoint = '{api_url}tracks/{track_id}'.format(
            api_url=API_URL, track_id=track_id)

        return requests.get(
            url=endpoint,
            headers={'Authorization': AUTH_TOKEN_FMT.format(
                self._access_token)})

    @spotify_request
    def get_player_info(self):
        """ Gets the current playing context """

        return requests.get(
            url='{api_url}me/player'.format(api_url=API_URL),
            headers={'Authorization': AUTH_TOKEN_FMT.format(
                self._access_token)})

    def vote(self, **kwargs):
        """ Override of the method from the DemocraticPlaylist to get the track info based on the
            ID of the track being voted """

        track_id = kwargs["track_uri"].split(":")[-1]
        track_info = None
        if track_id in tracks_cache:
            track_info = tracks_cache[track_id]
        else:
            track_info = self.get_track(track_id)

        # Call the method from the base class
        DemocraticPlaylist.vote(self, track_info)
