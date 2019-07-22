""" Wrappers to 'requests' """
import os
import time
import json
from urllib.parse import urlencode
from requests import get as _get, post as _post, exceptions

from frontend.utils.log import get_logger
logger = get_logger("frontend_debug")


HOST = os.environ.get("BACKEND_HOST", "127.0.0.1")
PORT = os.environ.get("BACKEND_PORT", 9001)
MAX_RETRIES = os.environ.get("BACKEND_MAX_RETRIES", 5)
ADDR = "http://{}:{}/".format(HOST, PORT)


def ping(max_retries=MAX_RETRIES):
    """ Check health """
    while True:
        try:
            endpoint = ADDR + "ping"
            r = _get(endpoint)
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


def post(backend_endpoint, max_retries=MAX_RETRIES, **payload):
    """ Send POST request to the backend """
    if not backend_endpoint:
        raise RuntimeError(
            "When trying to make a POST request to the backend: no endpoint was provided")
    while True:
        try:
            endpoint = ADDR + backend_endpoint
            logger.debug("POST request with payload: %s", payload)
            r = _post(endpoint, json=payload)
            r.raise_for_status()
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
            if max_retries == 0:
                raise RuntimeError(
                    "POST request to backend endpoint '{}' failed: {}".format(
                        endpoint, err))
            max_retries -= 1
            time.sleep(0.5)
            continue
        except exceptions.HTTPError as err:
            raise RuntimeError(
                "Error during POST request to backend endpoint '{}': {}".format(endpoint, err))
        logger.debug("POST response: %s", r.text)
        return r.json() if r.text else None


def get(backend_endpoint, max_retries=MAX_RETRIES, **payload):
    """ Send GET request to the backend """
    if not backend_endpoint:
        raise RuntimeError(
            "When trying to make a GET request to the backend: no endpoint was provided")

    while True:
        try:
            endpoint = ADDR + backend_endpoint
            logger.debug("Get payload: %s", urlencode(payload))
            r = _get(endpoint, params=urlencode(payload))
            r.raise_for_status()
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
            if max_retries == 0:
                raise RuntimeError(
                    "GET request to backend endpoint '{}' failed: {}".format(
                        endpoint, err))
            max_retries -= 1
            time.sleep(0.5)
            continue
        except exceptions.HTTPError as err:
            raise RuntimeError(
                "Error during GET request to backend endpoint '{}': {}".format(
                    endpoint, err))
        logger.debug("Get response: %s", r.text)
        return r.json() if r.text else None
