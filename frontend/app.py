import os
import sys

from flask import Flask, session, url_for, request, redirect, render_template

from frontend.player import player as player_blueprint
from frontend.utils.request_helpers import ping as ping_backend, get
from frontend.utils.simple_kv_helpers import ping as ping_simple_kv


def getFrontendFlaskApp():
    """ Creates and configures a new Flask app that will be used to run the
        frontend """

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "this is my super secret key"
    # This is specific to the Spotify proxy and should be moved to a separate file
    stage = "start_login"
    @app.before_request
    def initialize():
        """Ensures initialization of the backend before giving access to the player"""
        nonlocal stage

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

    # This blueprints takes care of the general pages: playlist, search, etc
    app.register_blueprint(
        player_blueprint, url_prefix="/")

    return app
