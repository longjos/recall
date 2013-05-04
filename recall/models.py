import uuid
import UserDict


class Command(UserDict.UserDict):
    pass


class Event(UserDict.DictMixin):
    def __init__(self, guid):
        self._data = {"guid": guid}

    def __getitem__(self, item):
        return self._data[item]

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()


class EntityList(UserDict.UserDict):
    def add(self, entity):
        self.update({entity.guid: entity})

    def _get_all_events(self):
        return tuple(x._get_all_events() for x in self.items())

    def _get_all_child_entities(self):
        return tuple(self.items())

    def _get_all_entities(self):
        return self._get_all_child_entities()


class Entity(object):
    """
    A domain entity. This is a base implementation of a domain model in the
    sense of Domain Driven Design by Eric Evans. This model is also event-
    sourced, supporting an event-driven style of architecture.
    """
    def __init__(self):
        self.guid = None
        self._version = 0
        self._events = []
        self._handlers = {}

    def _apply_event(self, event):
        self._handle_domain_event(event)
        self._events += [event]

    def _get_all_events(self):
        return (
            tuple(self._events)
            + tuple(x._get_all_events() for x in self._get_child_entities()))

    def _get_all_entities(self):
        return (self, ) + self._get_child_entities()

    def _get_child_entities(self):
        def flatten(that, this):
            return that + (
                tuple(this) if isinstance(this, EntityList) else tuple())

        return (
            tuple(entity for entity in dir(self) if isinstance(entity, Entity))
            + reduce(flatten, dir(self), tuple()))

    def _create_guid(self):
        return uuid.uuid4()

    def _handle_domain_event(self, event):
        event_cls = event.__class__
        if event_cls in self._handlers:
            self._handlers[event_cls](event)

    def _increment_version(self, amount=1):
        self._version += amount

    def _clear_events(self):
        self._events = []

    def _register_event_handler(self, event_cls, callback):
        self._handlers[event_cls] = callback


class AggregateRoot(Entity):
    pass