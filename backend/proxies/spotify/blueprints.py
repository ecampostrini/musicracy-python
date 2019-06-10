from urllib.parse import urlencode

from flask import Blueprint, redirect, url_for, request

from .constants import AUTH_URL, CALLBACK_ENDPOINT


def create_login_blueprint(client_id,
                           client_secret,
                           scope,
                           code_queue):
    """ Returns a bluerint that takes care of getting the permissions from
        the user to access Spotify """

    login_blueprint = Blueprint('login', __name__)

    request_data = {}
    request_data['grant_type'] = 'authorization_code'
    request_data['client_id'] = client_id
    request_data['client_secret'] = client_secret
    request_data['response_type'] = 'code'
    request_data['redirect_uri'] = CALLBACK_ENDPOINT
    request_data['scope'] = ' '.join(scope)

    auth_url = '{}:{}'.format(AUTH_URL, urlencode(request_data))

    @login_blueprint.route('/', methods=['GET'])
    def index():
        return redirect(auth_url, code=302)

    @login_blueprint.route('/callback', methods=['GET'])
    def callback():
        token = request.args.get('code', None)

        print('THE TOKEN {}'.format(token))

        code_queue.put(token)
        return redirect(url_for('player.login'))

    return login_blueprint
