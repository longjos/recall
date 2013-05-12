import copy
import json
import uuid

import redis

import recall.event_marshaler
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

    def _create_entity(self, entity):
        """
        Creates the array members for the entity if it is not found

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        assert isinstance(entity, recall.models.Entity)
        if not self._events.get(entity.guid):
            self._events[entity.guid] = []


class Redis(EventStore):
    """
    An Redis event store
    """

    def __init__(self, **kwargs):
        self._client = redis.StrictRedis(**kwargs)
        self._marshaler = recall.event_marshaler.DefaultEventMarshaler()

    def get_all_events(self, guid):
        """
        Get all events for a domain entity

        :param guid: The guid of the domain entity
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`iterator`
        """
        assert isinstance(guid, uuid.UUID)
        return self.get_events_from_version(guid, 0)

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

        def fix_up(event):
            return self._marshaler.unmarshal(json.loads(event))

        return (fix_up(e) for e in self._client.lrange(str(guid), version, -1))

    def save(self, entity):
        """
        Save a domain entity's events

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        assert isinstance(entity, recall.models.Entity)

        def fix_up(event):
            return json.dumps(self._marshaler.marshal(event))

        for provider in entity._get_all_entities():
            marshaled = tuple(fix_up(e) for e in provider._events)
            if marshaled:
                self._client.rpush(str(provider.guid), *marshaled)
