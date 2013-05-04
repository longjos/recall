import pickle


class SnapshotStore(object):
    def load(self, guid):
        raise NotImplementedError

    def save(self, entity):
        raise NotImplementedError


class Memory(SnapshotStore):
    def __init__(self):
        self._snapshots = {}

    def load(self, guid):
        snapshot = self._snapshots.get(guid)
        return pickle.loads(snapshot) if snapshot else None

    def save(self, entity):
        self._snapshots[entity.guid] = pickle.dumps(entity)