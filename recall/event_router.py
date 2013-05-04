

class EventRouter(object):
    def route(self, event):
        raise NotImplementedError


class StdOut(EventRouter):
    def route(self, event):
        print("[x] Routed event %s" % event.__class__.__name__)


class Callback(EventRouter):
    def __init__(self):
        self._handlers = {}

    def route(self, event):
        callback = self._handlers.get(event.__class__)
        if callback:
            callback(event)

    def register_event_handler(self, event_cls, callback):
        if not self._handlers.get(event_cls):
            self._handlers[event_cls] = []

        self._handlers[event_cls] += [callback]

    def clear_event_handlers(self, event_cls):
        self._handlers[event_cls] = []