""" Connects to Spotify's API and handles the refresh token
    automatically """

from urllib.parse import urlencode
import base64
import threading
import requests

from .constants import AUTH_URL, CALLBACK_ENDPOINT, TOKEN_URL


REFRESH_CONDITION = threading.Condition()  # Uses an RLock by default


class SpotifyConnector:
    """ Class that handles the authentication against Spotify and the
        automatic refresh of the access token
    """

    def __init__(self, **config):
        """ 'super' is called cause this class is part of the
            SpotifyClient mixin and all the constructors of mixin base classes
            should be called """

        super().__init__(**config)

        for required in [
                "CLIENT_ID", "CLIENT_SECRET", "USER_ID"]:
            if not required in config:
                raise RuntimeError(
                    "Required key is missing from the config: {}".format(
                        required))

        self.client_id = config['CLIENT_ID']
        self.client_secret = config['CLIENT_SECRET']
        self.user_id = config['USER_ID']

        self._refresh_token = None
        self._access_token = None
        self._auto_refresh = config.get('auto_refresh', True)
        self._refresh_thread = None
        self._refresh_thread_running = False

    def start_login(self, controller=None,
                    scope=('user-modify-playback-state',
                           'playlist-modify-private',
                           'user-read-playback-state')):
        """ Returns the URL used to authorize Spotify to access the playlist """

        authentication_params = {}
        authentication_params['grant_type'] = 'authorization_code'
        authentication_params['client_id'] = self.client_id
        authentication_params['client_secret'] = self.client_secret
        authentication_params['response_type'] = 'code'
        authentication_params['redirect_uri'] = CALLBACK_ENDPOINT
        authentication_params['scope'] = ' '.join(scope)

        authentication_url = "{}?{}".format(
            AUTH_URL, urlencode(authentication_params))

        # This response goes all the way up to the front-end which expects JSON
        return {"location": authentication_url}

    def complete_login(self, **kwargs):
        """Gets the parameters back from Spotify after a successful login"""

        if "code" not in kwargs:
            raise RuntimeError(
                "Refresh token is missing. I cannot connect to Spotify")

        # Store the code to perform token refreshing in the future and
        # ask an access token for the first time
        self._refresh_token = kwargs["code"]
        self.refresh_token(first_time=True)

        if self._auto_refresh and not self._refresh_thread_running:
            # Lauch a thread to automatically refresh the access token when it's
            # about to expire
            self._refresh_thread = threading.Thread(target=self._refresh_worker)
            self._refresh_thread.start()
            self._refresh_thread_running = True

    def refresh_token(self, first_time=False):
        """
        Get a new access token

        Parameters
        ----------
        first_time: bool
          If True then the value in self._refresh_token is used as the authorization code.
          Otherwise it is used as the refresh token
        """

        with REFRESH_CONDITION:
            request_data = {}
            if first_time:
                request_data['grant_type'] = 'authorization_code'
                request_data['code'] = self._refresh_token
                request_data['redirect_uri'] = CALLBACK_ENDPOINT
                request_data['client_id'] = self.client_id
                request_data['client_secret'] = self.client_secret
                r = requests.post(url=TOKEN_URL, data=request_data)
            else:
                request_data['grant_type'] = 'refresh_token'
                request_data['refresh_token'] = self._refresh_token
                client_id_secret = '{}:{}'.format(
                    self.client_id, self.client_secret)
                headers = {'Authorization': 'Basic {}'.format(
                    base64.b64encode(client_id_secret.encode()).decode())}
                r = requests.post(
                    url=TOKEN_URL, headers=headers, data=request_data)

            r.raise_for_status()
            refresh_response = r.json()

            # logger.debug('refresh_token answer from server: %s',
            #  refresh_response)

            if first_time:
                self._refresh_token = refresh_response.get(
                    'refresh_token', None)
            self._access_token = refresh_response.get('access_token', None)
            self._expires_in = refresh_response.get('expires_in', None)

            # logger.info('refresh token expires in: %s', self._expires_in)
            # logger.info('new access token %s', self._access_token)

    def _refresh_worker(self):
        """
        Sleep int(_expires_in - 15) seconds and try to refresh the token on thread wake up
        """

        while True:
            REFRESH_CONDITION.acquire()
            was_notified = REFRESH_CONDITION.wait(float(self._expires_in - 15))
            if was_notified or not self._refresh_thread_running:
                # Time to leave
                # logger.info('Spotify token-refresh thread exiting')
                break
            # logger.info('Spotify token being refreshed by token-refresh thread')
            self.refresh_token(False)
            REFRESH_CONDITION.release()

    def finish(self):
        """
        Clean-up: notify the refresh worker, make it exit and join it
        """

        if self._refresh_thread_running:
            self._refresh_thread_running = False
            if self._refresh_thread.is_alive():
                # logger.info('Shutting down Spotify token-refresh thread')
                REFRESH_CONDITION.acquire()
                REFRESH_CONDITION.notify_all()
                REFRESH_CONDITION.release()
                self._refresh_thread.join()
            else:
                pass
                # logger.warning(
                #     'During clean-up: Spotify token-refresh thread marked as '
                #     'running but not alive. Will mark it as not running')
