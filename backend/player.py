""" Defines the Player class that coordinates all necessary components from the
    backend """
from backend.controller import Controller


class Player:
    """ Exposes the player interface and coordinates the underlying components """

    def __init__(self, proxy):
        self.proxy = proxy.get_client()
        self.controller = Controller(self.proxy)
        self.controller.start()

    def play(self):
        """ Enqueues a PLAY event """
        return self.proxy.play()

    def pause(self):
        """ Enqueues a PAUSE event """
        return self.proxy.pause()

    def search(self, *options, **filters):
        """ Forwards the filters to the searcher and returns the search result """
        return self.proxy.search(*options, **filters)

    def get_playlist(self):
        """Returns an dictionary containing the tracks from the playlist along
           with the amount of votes each track has
        """
        return self.proxy.get_playlist()

    def vote(self, *args, **kwargs):
        """ Adds a vote to the track with id track_id """
        return self.proxy.vote(*args, **kwargs)

    def finish(self):
        """ Shuts down all components """
        if hasattr(self.proxy, "finish"):
            self.proxy.finish()

    def register_proxy_method(self, f):
        """ Registers a new method to the current instance. Used to customize the
            Player object with methods that are specific to the backend.
            'f' MUST be a method from the proxy being used
        """

        from functools import wraps
        @wraps(f)
        def new_method(*args, **kwargs):
            return f(self.proxy, controller=self.controller, *args, **kwargs)

        setattr(self, f.__name__, new_method)
