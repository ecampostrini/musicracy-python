""" Renames and exposes the client along with any extra endpoint
    adhering to the "convention"
"""

from .client import SpotifyClient
from .config import CONFIG
from .endpoints import EXTRA_ENDPOINTS


def get_extra_endpoints():
    """ Returns a list of extra endponits (along with the extra Player methods that
        handle them) that are to be added to the backend server as well as to the
        Player
    """
    return EXTRA_ENDPOINTS


def get_client():
    """ Very small factory that creates an instance of the client,
        taking care of whatever internal configuration that may be required
    """
    return SpotifyClient(**CONFIG)
