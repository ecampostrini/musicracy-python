""" This module contains the definitions of the Flask forms """

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SearchForm(FlaskForm):
    """ Flask form used for searchin a song """
    track_name = StringField('Song Name:')
    artist_name = StringField('Artist:')
    album_name = StringField('Album:')
    submit = SubmitField('Search')
