import copy
import uuid

import recall.models


class EventStore(object):
    """
    The Event Store interface
    """
    def get_all_events(self, guid):
        """
        Get all events for a domain entity

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`iterator`
        """
        assert isinstance(guid, uuid.UUID)
        raise NotImplementedError

    def get_events_from_version(self, guid, version):
        """
        Get events for a domain entity as of a given version

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :param version: The version of the domain entity
        :type version: :class:`int`

        :rtype: :class:`iterator`
        """
        assert isinstance(guid, uuid.UUID)
        assert isinstance(version, int)
        raise NotImplementedError

    def get_type(self, guid):
        """
        Get the type of a domain entity

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`type`
        """
        assert isinstance(guid, uuid.UUID)
        raise NotImplementedError

    def save(self, entity):
        """
        Save a domain entity's events

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        assert isinstance(entity, recall.models.Entity)
        raise NotImplementedError


class Memory(EventStore):
    """
    An in-memory event store
    """
    def __init__(self):
        self._events = {}
        self._entities = {}

    def get_all_events(self, guid):
        """
        Get all events for a domain entity

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`iterator`
        """
        assert isinstance(guid, uuid.UUID)
        return self._events.get(guid)

    def get_events_from_version(self, guid, version):
        """
        Get events for a domain entity as of a given version

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :param version: The version of the domain entity
        :type version: :class:`int`

        :rtype: :class:`iterator`
        """
        assert isinstance(guid, uuid.UUID)
        assert isinstance(version, int)
        return (self._events.get(guid) or [])[version:]

    def get_type(self, guid):
        """
        Get the type of a domain entity

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`type`
        """
        assert isinstance(guid, uuid.UUID)
        return self._entities[guid]['type']

    def save(self, entity):
        """
        Save a domain entity's events

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        assert isinstance(entity, recall.models.Entity)
        for provider in entity._get_all_entities():
            self._create_entity(provider)
            for event in provider._events:
                self._events[provider.guid].append(copy.copy(event))
                self._increment_version(provider.guid)

    def _create_entity(self, entity):
        """
        Creates the array members for the entity if it is not found

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        assert isinstance(entity, recall.models.Entity)
        if not self._entities.get(entity.guid):
            self._entities[entity.guid] = {
                "type": entity.__class__,
                "version": 0
            }

        if not self._events.get(entity.guid):
            self._events[entity.guid] = []

    def _increment_version(self, guid):
        """
        Updates the local copy of the domain entity's version

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`
        """
        assert isinstance(guid, uuid.UUID)
        self._entities[guid]["version"] += 1
