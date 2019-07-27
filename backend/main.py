"""Implement the service that exposes the API from the player"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qsl
from importlib import import_module
import sys
import json
import os

from backend.utils.log import get_logger
from backend.utils.simple_kv_helpers import ping as ping_simple_kv
from player import Player

HOSTNAME = os.environ.get("BACKEND_HOSTNAME", "0.0.0.0")
PORT = int(os.environ.get("BACKEND_PORT", "9001"))

logger = get_logger("backend")


def makeError(msg):
    """Return a JSON error object with the msg passed as argument
    """
    return json.dumps({"error": msg})


def getHandler(player):
    """ Instantiates a new request handler that uses the given backend_instance
        to process the requests
    """
    class Handler(BaseHTTPRequestHandler):
        """HTTP handler that parses requests and passes them on to the player
        """

        endpoints = {}
        player = player

        @classmethod
        def register_endpoint(cls, name, func, method="GET"):
            """Register a new endpoint and it's corresponding function"""

            method = method.upper()
            if method not in ["GET", "POST"]:
                raise RuntimeError(
                    "Trying to register endpoint {} with a non-supported "
                    "method {}".format(name, method))

            if name in cls.endpoints:
                logger.error(
                    "Trying to register and endpoint that already exists: %s",
                    name)
                raise RuntimeError(
                    "Endpoint with name {} already exists".format(name))

            cls.endpoints[(name, method)] = func

        def output_headers(self):
            """Utility method that writes the JSON headers that goes in all succesful responses
            """

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

        def do_GET(self):
            """Unpacks the incoming GET requests and forwards them to the app
            """

            (scheme,
             netloc,
             path,  # The path is used to specify the action
             path_params,
             query,
             fragments) = urlparse(self.path)

            # In case the endpoint is a 3rd party one dispatch the request
            # to the propper function
            endpoint = (path, "GET")
            if endpoint in self.endpoints:
                self.endpoints[endpoint](self)
                return

            # Otherwise check if it is one of the standard endpoints
            if path == "/ping":
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"PONG")
                return

            if path == "/playlist":
                response = player.get_playlist()
                self.output_headers()
                self.wfile.write(json.dumps(response).encode())
                return

            if path == "/search":
                params = dict(parse_qsl(query))

                logger.debug("Calling search with parameters: %s", params)

                response = player.search(**params)
                self.output_headers()
                self.wfile.write(json.dumps(response).encode())
                return

            self.send_error(400, makeError(
                "No such GET endpoint: {}".format(path)))

        def do_POST(self):
            """Unpacks the incoming POST requests and forwards them to the app
            """

            (scheme,
             netloc,
             path,  # The path is used to specify the action
             path_params,
             query,
             fragments) = urlparse(self.path)

            # In case the endpoint is a 3rd party one dispatch the request
            # to the propper function
            endpoint = (path, "POST")
            if endpoint in self.endpoints:
                self.endpoints[endpoint](self)
                return

            if path == "/vote":
                raw_body = self.rfile.read(
                    int(self.headers.get("Content-Length")))
                obj = json.loads(raw_body)
                player.vote(**obj)
                self.send_response(204)
                self.end_headers()
                return

            if path == "/play":
                response = player.play()
                self.send_response(204)
                self.end_headers()
                return

            if path == "/pause":
                response = player.pause()
                self.send_response(204)
                self.end_headers()
                return

            self.send_error(400, "No such POST endpoint: {}".format(path))

    return Handler


class ThreadedServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread"""


def get_backend():
    backend_name = os.environ.get("MUSICRACY_BACKEND_NAME")
    if not backend_name:
        logger.error("MUSICRACY_BACKEND_NAME is not configured")
        sys.exit(1)
    return import_module('.'.join(['proxies', backend_name]))


if __name__ == '__main__':
    ping_simple_kv()

    backend = get_backend()
    player = Player(backend)
    handlerClass = getHandler(player)

    # Register additional endpoints specific to the selected backend
    for endpoint_info in backend.get_extra_endpoints():
        endpoint, method, handler, proxy_medhod = endpoint_info

        logger.debug("Registering extra proxy method: %s",
                     proxy_medhod.__name__)
        player.register_proxy_method(proxy_medhod)

        logger.debug(
            "Registering extra endpoint handler [%s]: %s", method, endpoint)
        handlerClass.endpoints[(endpoint, method)] = handler

    server = ThreadedServer((HOSTNAME, PORT), handlerClass)

    try:
        logger.debug("Starting server in address: %s:%s", HOSTNAME, PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        logger.debug("Shutting down...")
        server.shutdown()
        player.finish()
