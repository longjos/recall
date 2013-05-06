import datetime
import types
import uuid
import pika
import msgpack
import recall.models


class EventRouter(object):
    """
    The Event Router Interface

    This is a class of objects which know how and where to send events once they
    occur.
    """
    def route(self, event):
        """
        Route the event

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        assert isinstance(event, recall.models.Event)
        raise NotImplementedError


class StdOut(EventRouter):
    """
    Print meta information for an event
    """
    def route(self, event):
        """
        Print the event to stdout

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        assert isinstance(event, recall.models.Event)
        print("[x] Routed event %s" % event.__class__.__name__)


class Callback(EventRouter):
    """
    Handle an event with registered callbacks
    """
    def __init__(self):
        self._handlers = {}

    def route(self, event):
        """
        Handle the event with registered callbacks

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        assert isinstance(event, recall.models.Event)
        callback = self._handlers.get(event.__class__)
        if callback:
            callback(event)

    def register_event_handler(self, event_cls, callback):
        """
        Register a callback

        :param event_cls: The class object of the domain event
        :type event_cls: :class:`type`

        :param callback: The callback
        :type callback: :class:`types.FunctionType`
        """
        assert isinstance(event_cls, type(recall.models.Event))
        assert isinstance(callback, types.FunctionType)
        if not self._handlers.get(event_cls):
            self._handlers[event_cls] = []

        self._handlers[event_cls] += [callback]


class AMQP(EventRouter):
    """
    Publish an event via AMQP

    :param connection: The connection settings
    :type connection: :class:`dict`

    :param channel: The channel settings
    :type channel: :class:`dict`

    :param exchange: The exchange settings
    :type exchange: :class:`dict`
    """
    def __init__(self, connection=None, channel=None, exchange=None):
        assert isinstance(connection, dict) or isinstance(connection, types.NoneType)
        assert isinstance(channel, dict) or isinstance(channel, types.NoneType)
        assert isinstance(exchange, dict) or isinstance(exchange, types.NoneType)
        connection = connection or {}
        channel = channel or {}
        self.exchange = exchange or {}

        if "username" in connection and "password" in connection:
            connection["credentials"] = pika.PlainCredentials(
                username=connection["username"],
                password=connection["password"]
            )
            del(connection["username"])
            del(connection["password"])

        params = pika.ConnectionParameters(**connection)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel(**channel)
        self.channel.exchange_declare(**self.exchange)

    def _packer(self, obj):
        """
        Default packer for msgpack

        :param obj: The object to pack
        :type obj: :class:`object`

        :rtype: :class:`object`
        """
        if isinstance(obj, recall.models.Event):
            return {"__type__": obj.__class__.__name__, "data": obj._data}
        if isinstance(obj, datetime.datetime):
            return {"__datetime__": True, "datetime": obj.isoformat()}
        if isinstance(obj, uuid.UUID):
            return {"__uuid__": True, "uuid": str(obj)}
        return obj

    def route(self, event):
        """
        Publish the event

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        assert isinstance(event, recall.models.Event)
        self.channel.basic_publish(
            exchange=self.exchange.get("exchange", ""),
            routing_key=event.__class__.__name__,
            body=msgpack.packb(event, default=self._packer))