import copy


class EventStore(object):

    def get_all_events(self, guid):
        raise NotImplementedError

    def get_events_from_version(self, guid, version):
        raise NotImplementedError

    def get_type(self, guid):
        raise NotImplementedError

    def save(self, entity):
        raise NotImplementedError


class Memory(EventStore):
    def __init__(self):
        self._events = {}
        self._entities = {}

    def get_all_events(self, guid):
        return self._events.get(guid)

    def get_events_from_version(self, guid, version):
        assert isinstance(version, int)
        return (self._events.get(guid) or [])[version:]

    def get_type(self, guid):
        return self._entities[guid]['type']

    def save(self, entity):
        for provider in entity._get_all_entities():
            self._create_entity(provider)
            for event in provider._events:
                self._events[provider.guid].append(copy.copy(event))
                self._increment_version(provider.guid)

    def _create_entity(self, entity):
        if not self._entities.get(entity.guid):
            self._entities[entity.guid] = {
                "type": entity.__class__,
                "version": 0
            }

        if not self._events.get(entity.guid):
            self._events[entity.guid] = []

    def _increment_version(self, guid):
        self._entities[guid]["version"] += 1
