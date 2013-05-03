import copy


class SnapshotStore(object):
    def load(self, guid):
        raise NotImplementedError

    def save(self, entity):
        raise NotImplementedError


class Memory(SnapshotStore):
    def __init__(self):
        self._snapshots = {}

    def load(self, guid):
        return self._snapshots.get(guid)

    def save(self, entity):
        self._snapshots[entity.guid] = copy.copy(entity)