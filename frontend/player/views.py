from flask import render_template, request, redirect, url_for
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError

from frontend.app import session, db, get, post
from frontend.models import User, Vote
from frontend.app import get, post
from frontend.utils.log import get_logger

from .forms import SearchForm
from . import player

logger = get_logger("frontend_debug")


@player.before_request
def check_proxy_authentication():
    return
    # if not app_player.proxy_is_logged_in():
    #     # TODO or return error in case the login url is None
    #     return redirect(app_player.get_proxy_login_url())


@player.before_request
def check_valid_login():
    username = session.get('username', '')
    logged_in = User.query.filter_by(username=username).count() == 1
    if ((not len(username) or not logged_in) and
        not request.path.startswith('/static/') and
            not request.endpoint.endswith('login')):
        return redirect(url_for('player.login'))


@player.route('/', methods=['GET'])
def index():
    return redirect(url_for('player.playlist'))


@player.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', None)
        if not username:
            error = 'You must enter a username'
        elif User.query.filter_by(username=username).count():
            error = 'The username you entered is already taken'
        else:
            session['username'] = username
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('player.playlist'))

    return render_template('player/login.html', title='Login', error_text=error)


@player.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
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


@player.route('/playlist', methods=['GET'])
def playlist():
    username = session['username']
    user_votes = [vote.track_uri
                  for vote in Vote.query.filter_by(username=username)]
    # TODO (maybe?) allow pagination in case the list of songs is too large

    track_info_list = get("playlist")
    track_info_list = track_info_list["result"] if track_info_list else []

    return render_template('player/playlist.html',
                           title='Democratic playlist',
                           songs=track_info_list,
                           voted_tracks=user_votes,
                           search_form=SearchForm())


@player.route('/vote/<track_id>', methods=['POST'])
def vote(track_id):
    username = session['username']

    try:
        vote = Vote(track_uri=track_id, username=username)
        db.session.add(vote)
        db.session.commit()

        post("vote", **{"track_uri": track_id})
    except InvalidRequestError:
        error_msg = 'You are trying to vote a song twice, that\'s not allowed'
    except SQLAlchemyError:
        error_msg = 'Ups! Something went wrong while voting/adding the song'

    # TODO add banner somewhere on the playlist page in case song couldn't be added
    return redirect(url_for('player.playlist'))


@player.route('/play')
def play():
    post("play")
    return 'Is playing baby !'


@player.route('/pause')
def pause():
    post("pause")
    return 'I just paused it baby !'
