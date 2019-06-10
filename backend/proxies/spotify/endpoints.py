""" This modules defines endpoint processing functions and associates them
    to the respective method from the proxy that is in charge of processing
    the request.
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qsl

from .client import SpotifyClient


def start_login_handler(httpHandler: BaseHTTPRequestHandler):
    """Used to handle the start of the authorization with Spotify"""

    response = httpHandler.player.start_login()
    httpHandler.output_headers()
    httpHandler.wfile.write(json.dumps(response).encode())
#     httpHandler.wfile.write(json.dumps(
#         {"Hi": "From the dynamically generated handler :)"}).encode())


def complete_login_handler(httpHandler: BaseHTTPRequestHandler):
    """Used to hanbdle the completion of the authorization with Spotify"""
    query = urlparse(httpHandler.path)[4]
    query_dict = dict(parse_qsl(query))
    httpHandler.player.complete_login(**query_dict)
    httpHandler.output_headers()


def initialize_handler(httpHandler: BaseHTTPRequestHandler):
    """Used to initialize the remote playlist via Spotify's API"""
    response = httpHandler.player.initialize()
    httpHandler.output_headers()
    httpHandler.wfile.write(json.dumps(response).encode())


EXTRA_ENDPOINTS = [
    ("/start_login", "GET", start_login_handler, SpotifyClient.start_login),
    ("/complete_login", "GET", complete_login_handler, SpotifyClient.complete_login),
    ("/initialize", "GET", initialize_handler, SpotifyClient.initialize),
]
