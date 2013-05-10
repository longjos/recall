import datetime
import uuid


class EventMarshaler(object):
    def marshal(self, event):
        """
        Marshal a domain event to a structure of built-in types

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        raise NotImplementedError()


class DefaultEventMarshaler(EventMarshaler):
    def _to_builtin(self, obj):
        """
        Convert an object to a type consisting of only built-in types

        :param obj: The object to convert
        :type obj: :class:`object`

        :rtype: :class:`object`
        """
        if isinstance(obj, dict):
            return {k: self._to_builtin(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return (self._to_builtin(v) for v in obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return {"__datetime__": True, "datetime": obj.isoformat()}
        if isinstance(obj, uuid.UUID):
            return {"__uuid__": True, "uuid": str(obj)}
        return obj

    def marshal(self, event):
        """
        Marshal a domain event to a structure of built-in types

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        return {
            "__type__": event.__class__.__name__,
            "data": self._to_builtin(event._data)}
