""" Wrappers to 'requests' """
import os
import time
import json
from urllib.parse import urlencode
from requests import get, post, exceptions

from frontend.utils.log import get_logger
logger = get_logger("frontend_debug")


def get_requests_helpers():
    """ Binds the address of the backend to a function to use it as a request
        dispatcher """

    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    port = os.environ.get("BACKEND_PORT", 9001)
    addr = "http://{}:{}/".format(host, port)

    def PING():
        """ Check health """
        max_retries = 5
        while True:
            try:
                endpoint = addr + "ping"
                r = get(endpoint)
                r.raise_for_status()
            except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
                if max_retries == 0:
                    raise RuntimeError(
                        "PING to backend failed after {} attempts: {}".format(
                            5, err))
                time.sleep(0.5)
                max_retries -= 1
                continue
            except exceptions.HTTPError as err:
                raise RuntimeError(
                    "PING to backend failed with error: {}".format(err))
            return

    def POST(backend_endpoint, **payload):
        """ Send POST request to the backend """
        if not backend_endpoint:
            raise RuntimeError(
                "When trying to make a POST request to the backend: no endpoint was provided")
        retries = 5
        while True:
            try:
                endpoint = addr + backend_endpoint
                logger.debug("POST request with payload: %s", payload)
                r = post(endpoint, json=payload)
                r.raise_for_status()
            except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
                if retries == 0:
                    raise RuntimeError(
                        "POST request to backend endpoint '{}' failed: {}".format(endpoint, err))
                retries -= 1
                time.sleep(0.5)
                continue
            except exceptions.HTTPError as err:
                raise RuntimeError(
                    "Error during POST request to backend endpoint '{}': {}".format(endpoint, err))
            logger.debug("POST response: %s", r.text)
            return r.json() if r.text else None

    def GET(backend_endpoint, **payload):
        """ Send GET request to the backend """
        if not backend_endpoint:
            raise RuntimeError(
                "When trying to make a GET request to the backend: no endpoint was provided")

        retries = 5
        while True:
            try:
                endpoint = addr + backend_endpoint
                logger.debug("Get payload: %s", urlencode(payload))
                r = get(endpoint, params=urlencode(payload))
                r.raise_for_status()
            except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
                if retries == 0:
                    raise RuntimeError(
                        "GET request to backend endpoint '{}' failed: {}".format(endpoint, err))
                retries -= 1
                time.sleep(0.5)
                continue
            except exceptions.HTTPError as err:
                raise RuntimeError(
                    "Error during GET request to backend endpoint '{}': {}".format(endpoint, err))
            logger.debug("Get response: %s", r.text)
            return r.json() if r.text else None

    return PING, POST, GET
