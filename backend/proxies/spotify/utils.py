""" Contains the definitions of several utility functions used by the Spotify client """

import requests
from time import sleep

from backend.utils.backend_adapter import BackendAdapter, TrackInfo, AlbumInfo, ArtistInfo
from backend.utils.log import get_logger

logger = get_logger("backend")


def gen_playlist_name():
    """ Generates a name for the playlist based on a timestamp """

    import time
    tm = time.gmtime(time.time())
    return 'musicracy-{}{}{}{}{}{}'.format(tm.tm_year, tm.tm_mon,
                                           tm.tm_mday, tm.tm_hour,
                                           tm.tm_min, tm.tm_sec)


def spotify_request(f):
    """ Wrapper to be used on methods from SpotifyClient which provides
        uniform error handling and helps to avoid repeating the
        same code all over the place """
    from functools import wraps
    @wraps(f)
    def with_exception_handling(self, *args, **kwargs):
        try:
            response = f(self, *args, **kwargs)
            response.raise_for_status()

            # TODO improve the logging here
            # logger.debug("Response to %s:\n%s", f.__name__, response.json())
            return response.json() if response.text else None
        except requests.HTTPError as exc:
            if exc.response is None:
                msg = 'Empty response from Spotify'
            else:
                error = exc.response.json()
                message = error['error']['message']
                status = error['error']['status']
                msg = '{} (Status: {})'.format(message, status)
            raise RuntimeError('{} request failed with error message: '
                               '{}'.format(f.__name__, msg)) from exc
        except Exception as exc:
            raise RuntimeError('Local processing of {} request '
                               'failed'.format(f.__name__)) from exc
    return with_exception_handling


def wait_until_is_playing(spotify_client, max_attempts=20):
    """ Waits untils there's a Spotify device ready and reproducing the playback.
        Used as an ugly way/hack to overcome the limitations of the Spotify API
        described in https://github.com/spotify/web-api/issues/462 """

    number_of_attempts = 0
    while True:
        player_info = spotify_client.get_player_info()
        number_of_attempts += 1
        if player_info['is_playing']:
            break

        if number_of_attempts > max_attempts:
            raise RuntimeError(
                'Reached the maximum number of checks ({}) '
                'of the state of the player'.format(max_attempts))
        sleep(1)
