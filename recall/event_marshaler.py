import datetime
import uuid

import recall.locators


class EventMarshaler(object):
    def marshal(self, event):
        """
        Marshal a domain event to a structure of built-in types

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        raise NotImplementedError()


class DefaultEventMarshaler(EventMarshaler):
    def __init__(self):
        self._locator = recall.locators.Locator({})

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

    def _from_builtin(self, obj):
        """
        Convert an object from a type consisting of only built-in types

        :param obj: The object to convert
        :type obj: :class:`object`

        :rtype: :class:`object`
        """
        if isinstance(obj, dict) and "__datetime__" in obj:
            return datetime.datetime.strptime(
                obj["datetime"],
                "%Y-%m-%dT%H:%M:%S.%f")
        if isinstance(obj, dict) and "__uuid__" in obj:
            return uuid.UUID("urn:uuid:%s" % obj["uuid"])
        if isinstance(obj, dict):
            return {k: self._from_builtin(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return (self._from_builtin(v) for v in obj)
        return obj

    def marshal(self, event):
        """
        Marshal a domain event to a structure of built-in types

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        return {
            "__type__": ".".join([event.__module__, event.__class__.__name__]),
            "data": self._to_builtin(event._data)}

    def unmarshal(self, marshaled):
        """
        Marshal a domain event to a structure of built-in types

        :param marshaled: A domain event marshaled to builtin types
        :type marshaled: :class:`object`
        """
        fqcn = marshaled["__type__"]
        class_name = fqcn.split(".")[-1]
        module_name = ".".join(fqcn.split(".")[0:-1])
        mdl = __import__(module_name, globals(), locals(), [class_name], 0)
        if class_name not in dir(mdl):
            raise NameError("Could not instantiate %s" % fqcn)
        cls = getattr(mdl, class_name)
        return cls(**self._from_builtin(marshaled["data"]))
