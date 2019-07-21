import os
import json
import time
from requests import get, post, exceptions
from urllib.parse import urlencode

from frontend.utils.log import get_logger

logger = get_logger("frontend_debug")

SIMPLE_KV_HOST = os.environ.get("SIMPLE_KV_HOST", "simple_kv")
SIMPLE_KV_PORT = os.environ.get("SIMPLE_KV_PORT", 5002)
MAX_RETRIES = os.environ.get("SIMPLE_KV_MAX_RETRIES", 5)
SIMPLE_KV_URL = "http://{}:{}".format(SIMPLE_KV_HOST, SIMPLE_KV_PORT)


def ping(max_retries=MAX_RETRIES):
    while True:
        try:
            logger.debug("Pinging the simpleKV to %s:%s",
                         SIMPLE_KV_HOST, SIMPLE_KV_PORT)
            r = get(SIMPLE_KV_URL + "/ping")
            r.raise_for_status()
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
            if max_retries == 0:
                raise RuntimeError(
                    "PING to simple-kv failed after {} attempts: {}".format(
                        5, err))
            time.sleep(0.5)
            max_retries -= 1
            continue
        except exceptions.HTTPError as err:
            raise RuntimeError(
                "PING to simple-kv failed with error: {}".format(err))
        return


def store(key, value, max_retries=MAX_RETRIES):
    while True:
        try:
            r = post(
                SIMPLE_KV_URL,
                json={"key": key, "value": value, "action": "create"})
            r.raise_for_status()
            return r.json() if r.text else None
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
            if max_retries == 0:
                raise RuntimeError(
                    "POST request to simple-kv endpoint '{}' failed: {}".format(
                        SIMPLE_KV_URL, err))
            max_retries -= 1
            time.sleep(0.5)
            continue
        except exceptions.HTTPError as e:
            msg = str(e)
            if e.response is not None:
                msg = msg + ". Response body: " + e.response.text
            logger.error(
                "Error while storing value in simple-kv: %s", msg)


def retrieve(key, max_retries=MAX_RETRIES):
    while True:
        try:
            r = get(SIMPLE_KV_URL, params=urlencode({"key": key}))
            r.raise_for_status()
            # TODO remove this log
            logger.debug("Retrieve got this: %s", r.json())
            return r.json() if r.text else None
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as err:
            if max_retries == 0:
                raise RuntimeError(
                    "GET request to simple-kv endpoint '{}' failed: {}".format(
                        SIMPLE_KV_URL, err))
            max_retries -= 1
            time.sleep(0.5)
            continue
        except exceptions.HTTPError as e:
            msg = str(e)
            if e.response is not None:
                msg = msg + ". Response body: " + e.response.text
            logger.error(
                "Error while retrieving from simple-kv: %s", msg)

    return ping, store, retrieve
