import os
import sys

from flask import Flask, session, url_for, request, redirect, render_template

from frontend.player import player as player_blueprint
from frontend.utils.request_helpers import ping as ping_backend, get
from frontend.utils.simple_kv_helpers import ping as ping_simple_kv
from frontend.utils.log import get_logger


logger = get_logger("frontend")


def no_proxy_url_error(error, endpoint, **values):
    """ Url error handler to redirect to the main application url
        in case the backend proxy didn't register any blueprint """
    return url_for('player.index')


app = Flask(__name__)

app.config["SECRET_KEY"] = "this is my super secret key"

# Request helpers available to the blueprints below

stage = "start_login"
@app.before_request
def initialize():
    """Ensures initialization of the backend before giving access to the player"""
    global stage

    if stage == "ready":
        return None

    if stage == "start_login":
        print("HERE!")
        location = get("start_login")["location"]
        stage = "complete_login"

        return redirect(location)

    if stage == "complete_login":
        code = request.args.get("code", None)
        get("complete_login", **{"code": code})
        stage = "initialize"

        return redirect(url_for("player.playlist"))

    if get("initialize")["is_playing"]:
        stage = "ready"
        return None

    return render_template("proxy/init_instructions.html")


#  Blueprints:
# proxy_blueprint = get_proxy_blueprint()
player_blueprint_url_prefix = '/'
# if proxy_blueprint is not None:
# This one belongs to the backend proxy being used and it's not always present.
# For example, the Spotify proxy registers some endpoints to deal with the
# user authentication
# app.register_blueprint(proxy_blueprint, url_prefix='/')
# player_blueprint_url_prefix = '/player'

# This one takes care of the general pages: playlist, search, etc
app.register_blueprint(player_blueprint, url_prefix=player_blueprint_url_prefix)

# Not sure if this is necessary
# app.url_build_error_handlers.append(no_proxy_url_error)

if __name__ == "__main__":
    try:
        ping_backend()
        ping_simple_kv()
    except Exception as e:
        logger.error("Exception during initialization: %s", str(e))
        sys.exit(1)
    app.run(host="0.0.0.0", port=5000)
