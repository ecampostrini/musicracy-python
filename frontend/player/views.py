from flask import render_template, request, redirect, url_for

from frontend.app import session
from frontend.utils.log import get_logger
from frontend.utils.request_helpers import get, post
from frontend.utils.simple_kv_helpers import retrieve, store

from .forms import SearchForm
from . import player

logger = get_logger("frontend_debug")


@player.route('/', methods=['GET'])
def index():
    return redirect(url_for('player.playlist'))


@player.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "GET":
        form = SearchForm()
        return render_template(
            'player/search.html', title='Search', search_form=form)

    filters = {'track': request.form.get('track_name', ''),
               'artist': request.form.get('artist_name', ''),
               'album': request.form.get('album_name', '')}

    payload = {**filters, **{"limit": 3, "item_type": "track"}}

    logger.debug("search payload: %s", payload)
    result = get("search", **payload)["result"]
    logger.debug("Search result: %s", result)

    return render_template('player/search_results.html',
                           title='Search results',
                           track_list=result)


@player.route("/playlist", methods=["GET"])
def playlist():
    try:
        user_votes = retrieve(request.remote_addr)["value"]
        track_info_list = get("playlist").get("result", [])

        return render_template(
            "player/playlist.html", title="Democratic playlist",
            songs=track_info_list, voted_tracks=user_votes,
            search_form=SearchForm())
    except RuntimeError as e:
        logger.error("Exception caught while retrieving playlist: %s", str(e))
        # Return None for the time being
        return None


@player.route("/vote/<track_id>", methods=["POST"])
def vote(track_id):
    try:
        if track_id not in retrieve(request.remote_addr)["value"]:
            store(request.remote_addr, track_id)
            post("vote", **{"track_id": track_id})
        return redirect(url_for("player.playlist"))
    except RuntimeError as e:
        logger.error("Exception caught while processing vote: %s", str(e))
        return redirect(url_for("player.playlist"))


@player.route('/play')
def play():
    post("play")
    return 'Is playing baby !'


@player.route('/pause')
def pause():
    post("pause")
    return 'I just paused it baby !'
