import itertools
import uuid
import UserDict


class Command(UserDict.UserDict):
    """
    A command object. Not to be confused with the command pattern. This object
    is simply used to shuttle data between the client and the write model.
    Conceptually, it represents the client instructing the domain to perform
    some action which may or may not result in a state change in the domain. In
    practice, it's a :class:`dict`, though it should be assumed to be immutable.
    """
    pass


class Event(UserDict.DictMixin):
    """
    An event object. This object is simply used to shuttle data between the
    write model and the read model. Conceptually, it represents a state change
    in the domain. In practice, it's a :class:`dict`, though it should be
    assumed to be immutable.

    IMPORTANT: An event can never be rejected (though it can be ignored). This
    represents a *change which has already happened* -- rejecting it would
    imply history can be re-written.

    :param guid: The guid of the domain entity
    :type guid: :class:`uuid.UUID`
    """
    def __init__(self, guid):
        self._data = {"guid": guid}

    def __getitem__(self, guid):
        """
        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`object`
        """
        return self._data[guid]

    def keys(self):
        """
        :rtype: :class:`iterator`
        """
        return self._data.keys()

    def items(self):
        """
        :rtype: :class:`iterator`
        """
        return self._data.items()


class EntityList(UserDict.UserDict):
    """
    A collection of domain entities, implemented as a :class:`dict` to allow
    random-access by key.
    """
    def add(self, entity):
        """
        Add an entity to the collection

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        self.update({entity.guid: entity})

    def get_all_events(self):
        """
        Get a flattened list of all the events for all the entities of the
        collection.

        :rtype: :class:`iterator`
        """
        return itertools.chain.from_iterable(
            x._events for x in self._get_all_entities())

    def _get_child_entities(self):
        """
        Get a flattened list of all the child entities of the collection.

        :rtype: :class:`iterator`
        """
        return itertools.chain.from_iterable(
            x._get_all_entities() for x in self.values()
            if isinstance(x, EntityList) or isinstance(x, Entity))

    def _get_all_entities(self):
        """
        Get a flattened list of all the child entities of the collection.

        :rtype: :class:`iterator`
        """
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

    def get_all_events(self):
        """
        Get a flattened list of all the events for all the entities of the
        collection.

        :rtype: :class:`iterator`
        """
        return itertools.chain.from_iterable(
            x._events for x in self._get_all_entities())

    def _apply_event(self, event):
        """
        Applies a domain event to a domain entity, i.e. performs the represented
        state change, and stages the event for storage. At this point, the state
        has changed, but no data has been persisted to the event store, i.e.
        this is a non-authoritative change.

        :param event: The event to apply
        :type event: :class:`recall.models.Event`
        """
        self._handle_domain_event(event)
        self._events += [event]

    def _get_child_entities(self):
        """
        Get a flattened list of all the child entities of this entity.

        :rtype: :class:`iterator`
        """
        return itertools.chain.from_iterable(
            x._get_all_entities() for x in self.__dict__.values()
            if isinstance(x, EntityList) or isinstance(x, Entity))

    def _get_all_entities(self):
        """
        Get a flattened list of this entity and all the child entities of this
        entity.

        :rtype: :class:`iterator`
        """
        return itertools.chain([self], self._get_child_entities())

    def _create_guid(self):
        """
        Create an entity GUID

        :rtype: :class:`uuid.UUID`
        """
        return uuid.uuid4()

    def _handle_domain_event(self, event):
        """
        Applies a domain event to a domain entity (non-authoritative).

        :param event: The event to apply
        :type event: :class:`recall.models.Event`
        """
        event_cls = event.__class__
        if event_cls in self._handlers:
            self._handlers[event_cls](self)(event)

    def _increment_version(self, amount=1):
        """
        Increments a domain entity's version by the given amount

        :param amount: The amount to increment
        :type amount: :class:`int`
        """
        self._version += amount

    def _clear_events(self):
        """
        Removes a domain entity's staged events.
        """
        self._events = []

    def _register_event_handler(self, event_cls, callback):
        """
        Register a domain event handler for an event

        :param event_cls: The event type to handle
        :type event_cls: :class:`type`

        :param callback: The callback class
        :type callback: :class:`recall.event_handler.DomainEventHandler`
        """
        self._handlers[event_cls] = callback


class AggregateRoot(Entity):
    """
    An aggregate root. This represents a single entity which may or may not
    contain an object graph which represents a logical and cohesive group of
    domain models.

    http://www.udidahan.com/2009/06/29/dont-create-aggregate-roots/
    """
    pass