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
        return reduce(lambda x, y: x + tuple(y._events), self._get_all_entities(), tuple())

    def _get_child_entities(self):
        def flatten(that, this):
            return that + (
                this._get_all_entities()
                if isinstance(this, EntityList) or isinstance(this, Entity)
                else tuple())

        return reduce(flatten, self.values(), tuple())

    def _get_all_entities(self):
        return self._get_child_entities()


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
        return reduce(lambda x, y: x + tuple(y._events), self._get_all_entities(), tuple())

    def _get_all_entities(self):
        return (self, ) + self._get_child_entities()

    def _get_child_entities(self):
        def flatten(that, this):
            attr = getattr(self, this)
            return that + (
                attr._get_all_entities()
                if isinstance(attr, EntityList) or isinstance(attr, Entity)
                else tuple())

        return reduce(flatten, dir(self), tuple())

    def _create_guid(self):
        return uuid.uuid4()

    def _handle_domain_event(self, event):
        event_cls = event.__class__
        if event_cls in self._handlers:
            self._handlers[event_cls](self)(event)

    def _increment_version(self, amount=1):
        self._version += amount

    def _clear_events(self):
        self._events = []

    def _register_event_handler(self, event_cls, callback):
        self._handlers[event_cls] = callback


class AggregateRoot(Entity):
    pass