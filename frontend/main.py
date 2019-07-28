import sys

from frontend.app import getFrontendFlaskApp
from frontend.utils.simple_kv_helpers import ping as ping_simple_kv
from frontend.utils.request_helpers import ping as ping_backend
from frontend.utils.log import get_logger

logger = get_logger("frontend")


def getApp():
    try:
        ping_backend()
        ping_simple_kv()
        return getFrontendFlaskApp()
    except Exception as e:
        logger.error("Exception during initialization: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    app = getApp()
    app.run(host="0.0.0.0", port=5000)
