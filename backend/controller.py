from threading import Timer, Thread
from queue import Queue
import time

from backend.utils.log import get_logger

logger = get_logger("backend")

INITIALIZE = 'INITIALIZE'
PLAY = 'PLAY'
PAUSE = 'PAUSE'
STOP = 'STOP'
TIMERS_UP = 'TIMERS_UP'
FINISH = 'FINISH'

STATE_RUNNING = 'RUNNING'
STATE_PAUSED = 'PAUSED'
STATE_STOPPED = 'STOPPED'


class Controller(Thread):
    def __init__(self, client_proxy, preload_in_secs=15):
        # The important part of the state is composed by the following 2 members
        self._state = STATE_STOPPED
        self._remaining_in_secs = 0

        self.queue = Queue()
        self._timer = None
        self._preload_in_secs = preload_in_secs
        self._proxy = client_proxy
        self._current_event = None
        self._last_state_change_ts = None

        super(Controller, self).__init__()

    def run(self):
        running = True
        while running:
            message = self.queue.get()
            logger.debug("Got event: %s", message)
            if message == PLAY:
                self._current_event = PLAY
                self._play()
            elif message == PAUSE:
                self._current_event = PAUSE
                self._pause()
            elif message == STOP:
                self._current_event = STOP
                self._stop()
            elif message == TIMERS_UP:
                self._current_event = TIMERS_UP
                self._cleanup_timer()
            elif message == FINISH:
                self._current_event = FINISH
                self._cleanup()
                running = False

    def _play(self):
        if self._state == STATE_STOPPED:
            current_track = self._proxy.next()
            self._remaining_in_secs = (
                current_track.length - self._preload_in_secs
                if current_track.length > self._preload_in_secs else
                current_track.length - current_track.length * 0.05)
            self._proxy.add_track(current_track.id)
        elif self._current_event == TIMERS_UP:
            current_track = self._proxy.next()
            self._remaining_in_secs = current_track.length
            self._proxy.add_track(current_track.id)
        elif self._state == STATE_RUNNING:  # ignore if it's already playing
            return

        logger.info("Now playing: %s", self._proxy._current_track.name)
        logger.info("Remaining in secs: %s", self._remaining_in_secs)

        if self._state in [
                STATE_PAUSED, STATE_STOPPED] and self._current_event != INITIALIZE:
            self._proxy.play()

        self._timer = Timer(self._remaining_in_secs,
                            lambda x: x.queue.put(TIMERS_UP), (self, ))
        self._timer.start()
        self._last_state_change_ts = int(time.time())
        self._state = STATE_RUNNING

    def _pause(self):
        if self._state != STATE_RUNNING:
            return

        self._proxy.pause()
        now = int(time.time())
        self._remaining_in_secs = self._last_state_change_ts + self._remaining_in_secs - now
        self._last_state_change_ts = now
        self._timer.cancel()
        self._state = STATE_PAUSED

    def _stop(self):
        if self._state != STATE_RUNNING:
            return

        self._proxy.stop()
        self._remaining_in_secs = None
        self._last_state_change_ts = None
        self._timer.cancel()
        self._state = STATE_STOPPED

    def _cleanup(self):
        if self._timer is not None and self._timer.is_alive():
            self._timer.cancel()
            self._remaining_in_secs = 0

    def _cleanup_timer(self):
        if self._state != STATE_RUNNING:
            self._state = STATE_STOPPED
            return
        self._play()
