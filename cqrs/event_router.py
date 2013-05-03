

class EventRouter(object):
    def route(self, event):
        raise NotImplementedError

    def add_handler(self, event_cls, handler):
        raise NotImplementedError


class StdOut(EventRouter):
    def route(self, event):
        print("[x] Routed event %s" % event.__class__.__name__)

    def add_handler(self, event_cls, handler):
        print("[ ] Added handler %s for %s" % (handler.__class__.__name__, event_cls.__name__))