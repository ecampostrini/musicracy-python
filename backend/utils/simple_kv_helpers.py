import os
import time
from requests import get, post, exceptions

from backend.utils.log import get_logger

logger = get_logger("backend_debug")

SIMPLE_KV_HOST = os.environ.get("SIMPLE_KV_HOST", "simple_kv")
SIMPLE_KV_PORT = os.environ.get("SIMPLE_KV_PORT", 5002)
MAX_RETRIES = os.environ.get("SIMPLE_KV_MAX_RETRIES", 5)
SIMPLE_KV_URL = "http://{}:{}".format(SIMPLE_KV_HOST, SIMPLE_KV_PORT)


def ping(max_retries=MAX_RETRIES):
    """ Pings the Simple KV and retries up to MAX_RETRIES in case there's no answer """
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


def delete(value, max_retries=MAX_RETRIES):
    """ Performs remote call to the Simple KV to delete the given `value`
        from all the keys is associated to """
    while True:
        try:
            r = post(
                SIMPLE_KV_URL,
                json={"value": value, "action": "delete"})
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
                "Error while deleting value from simple-kv: %s", msg)
