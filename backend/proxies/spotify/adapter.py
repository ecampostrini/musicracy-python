""" This modules defines adapters to be used to translate the response from Spotify
    into JSON objects that can be interpreted by the frontend
"""

from collections import namedtuple

from backend.utils.backend_adapter import BackendAdapter, TrackInfo

UserDevice = namedtuple('UserDevice', ['name', 'type', 'id', 'is_active'])


def json_to_track_info(json):
    """ Returns a dict with the necessary info from the track """
    ret = {}
    ret["name"] = json["name"]
    ret["artist"] = json["artists"][0]["name"]
    ret["album"] = json["album"]["name"]
    ret["id"] = json["uri"]
    ret["length"] = int(json["duration_ms"]) / 1000    # Track length in seconds

    return ret


def search_adapter(json_response):
    """ Returns a [TrackInfo] || [AlbumInfo] || [ArtistInfo] based on the Json
        response from Spotify """

    def get_tracks():
        ret = {"result": []}
        for item in json_response['tracks']['items']:
            ret["result"].append(json_to_track_info(item))
        return ret

    def get_albums():
        ret = {"result": []}
        for item in json_response['albums']['items']:
            album = item['name']
            artist = item['artists'][0]['name']
            album_id = item['uri']
            ret["result"].append(
                {"album": album, "artist": artist, "album_id": album_id})
        return ret

    def get_artists():
        ret = {"result": []}
        for item in json_response['artists']['items']:
            artist = item['name']
            artist_id = item['uri']
            ret["result"].append({"artist": artist, "id": artist_id})
        return ret

    if json_response.get('tracks', None):
        return get_tracks()

    if json_response.get('albums', None):
        return get_albums()

    if json_response.get('artists', None):
        return get_artists()

    return json_response


def get_user_devices_adapter(json_response):
    """ Extract devices info from the json_response and returns [UserDevice] """

    if 'devices' in json_response:
        ret = {"result": []}
        for device in json_response['devices']:
            ret["result"].append(
                {"name": device["name"],
                 "type": device["type"],
                 "id": device["id"],
                 "is_active": device["is_active"]})
        return ret
    return json_response


def get_playlist_tracks_adapter(json_response):
    """ Extracts a playlist' list of tracks from the json_response and returns [TrackInfo] """

    ret = {"result": []}
    for item in json_response['items']:
        ret["result"].append(json_to_track_info(item["track"]))
    return ret


def get_track_adapter(json):
    """ Extracts a TrackInfo from json """
    return TrackInfo(
        json['name'],                       # Track name
        json['artists'][0]['name'],         # Artist
        json['album']['name'],              # Album name
        json['uri'],                        # Track id
        int(json['duration_ms']) / 1000)    # Track length in seconds


backend_adapter = BackendAdapter()
backend_adapter.adapter_registry['search'] = search_adapter
backend_adapter.adapter_registry['get_user_devices'] = get_user_devices_adapter
backend_adapter.adapter_registry['get_playlist'] = get_playlist_tracks_adapter
backend_adapter.adapter_registry['get_track'] = get_track_adapter
