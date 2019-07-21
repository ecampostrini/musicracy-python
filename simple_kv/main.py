""" Very simple key value storage with HTTP interface and support for the following
    operations: get, set. It's thread safe by means of locks """
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from threading import Lock
from collections import defaultdict
import json
import os

from simple_kv.utils import get_logger

logger = get_logger("simple_kv")

HOST = os.environ.get("SIMPLE_KV_HOST", "0.0.0.0")
PORT = int(os.environ.get("SIMPLE_KV_PORT", 5002))
MULTIFIELD_KEY_SEPARATOR = os.environ.get("MULTIFIELD_KEY_SEPARATOR", ",")


class SimpleKV:
    """ Thread-safe key-value storage exposing 2 operations: `store` and `retrieve` """

    def __init__(self):
        self.db = defaultdict(set)
        self.rw_lock = Lock()

    def store(self, key, value):
        """ Associates the given value to the given key """
        with self.rw_lock:
            self.db[key].add(value)

    def retrieve(self, key):
        """ Returns the set of values associated to the given `key`. Returns `None` in case
            the key has no elements associated to it"""
        with self.rw_lock:
            return self.db.get(key)

    def delete(self, value):
        """ Deletes the specified value from all the associated keys """
        with self.rw_lock:
            for v in self.db.values():
                v.discard(value)


db = SimpleKV()


class Handler(BaseHTTPRequestHandler):
    """Request handler for the kv storage. Through a simple API gives access to
       the supported operations: get, set """

    def do_GET(self):
        """Handles retrieval of info from the storage"""

        logger.debug("GET request: %s", self.path)

        (
            scheme,
            netloc,
            path,
            query,
            fragment
        ) = urlsplit(self.path)

        if path.lower().endswith("ping"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", "4")
            self.end_headers()
            self.wfile.write(b"PONG")
            return

        raw_key = parse_qs(query).get("key")
        if raw_key is None:
            self.send_response(400)
            self.end_headers()
            return

        raw_key = raw_key[0]
        key_as_tuple = tuple(raw_key.split(MULTIFIELD_KEY_SEPARATOR))
        value_set = db.retrieve(key_as_tuple) or []

        # if value_set is None:
        #     self.send_response(204)
        #     self.end_headers()
        # Return empty as default in case there's no value_set for the given tuple
        # return

        ret = {"key": raw_key, "value": [v for v in value_set]}
        content = json.dumps(ret).encode()

        logger.info("Response body: %s", content)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        """Handles insertion of new values. In case the key is already in the map,
           the existing value is overriden """

        logger.debug("POST request: %s", self.path)

        content_length = int(self.headers.get("Content-Length"))
        try:
            content = json.loads(self.rfile.read(content_length))

            logger.info("POST request body: %s", content)

            action = content["action"]
            if action not in ["create", "delete"]:
                self.output_error(
                    **{"reason": "Invalid action {}".format(action)})
            elif action == "create":
                key = tuple(content["key"].split(MULTIFIELD_KEY_SEPARATOR))
                value = content["value"]
                db.store(key, value)
                self.send_response(201)
                self.end_headers()
            else:  # action == "delete"
                db.delete(content["value"])
                self.send_response(204)
                self.end_headers()

        except json.JSONDecodeError as e:
            self.output_error(**{"reason": "Request contains invalid JSON"})
        except KeyError as e:
            self.output_error(
                **{"reason": "Missing mandatory field {}".format(str(e))})

    def output_error(self, error_code=400, **kwargs):
        msg = json.dumps(kwargs).encode()
        self.send_response(error_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(msg))
        self.end_headers()
        self.wfile.write(msg)


if __name__ == '__main__':
    address = (HOST, PORT)
    server = HTTPServer(address, Handler)

    try:
        logger.info("simple KV listening in HOST %s and PORT %s", HOST, PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down the kv-storage...")
        server.shutdown()
