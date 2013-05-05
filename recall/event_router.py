import datetime
import uuid
import pika
import msgpack
import recall.models


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


class AMQP(EventRouter):
    def __init__(self, **kwargs):
        connection = kwargs.get("connection") or {}
        channel = kwargs.get("channel") or {}
        self.exchange = kwargs.get("exchange") or {}
        params = pika.ConnectionParameters(**connection)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel(**channel)
        self.channel.exchange_declare(**self.exchange)

    def _packer(self, obj):
        if isinstance(obj, recall.models.Event):
            return {"__type__": obj.__class__.__name__, "event": obj.__dict__}
        if isinstance(obj, datetime.datetime):
            return {"__datetime__": True, "datetime": obj.isoformat()}
        if isinstance(obj, uuid.UUID):
            return {"__uuid__": True, "uuid": str(obj)}
        return obj

    def route(self, event):
        self.channel.basic_publish(
            exchange=self.exchange.get("exchange", ""),
            routing_key=event.__class__.__name__,
            body=msgpack.packb(event, default=self._packer))