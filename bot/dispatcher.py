import logging


class Dispatcher(object):
    def __init__(self, bot):
        super(Dispatcher, self).__init__()

        self.log = logging.getLogger(__name__)

        self.bot = bot
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def remove_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    def dispatch(self, event):
        # noinspection PyBroadException
        try:
            self.log.debug("Dispatching event '{}'.".format(event))
            for handler in (h for h in self.handlers if h.check(event=event, dispatcher=self)):
                handler.handle(event=event, dispatcher=self)
        except StopDispatching:
            self.log.debug("Caught '{}' exception, stopping dispatching.".format(StopDispatching.__name__))
        except Exception:
            self.log.exception("Exception while dispatching event!")


class StopDispatching(Exception):
    """ If raised from handler 'check' or 'handle' methods then dispatching will be stopped. """
    pass
