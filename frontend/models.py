from frontend.app import app, db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    votes = db.relationship('Vote', backref='author', lazy='dynamic')

    def repr(self):
        return '<User {}>'.format(self.username)


class Vote(db.Model):
    __tablename__ = 'vote'

    id = db.Column(db.Integer, primary_key=True)
    track_uri = db.Column(db.String(128), index=True)
    username = db.Column(db.Integer, db.ForeignKey('user.username'))

    __table_args__ = (db.UniqueConstraint(
        'track_uri', 'username', name='_track_user_uc'),)


db.create_all()
