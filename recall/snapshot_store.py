import pickle


class SnapshotStore(object):
    """
    The Snapshot Store interface

    A snapshot is a non-authoritative representation of an aggregate root as of
    a moment in time. It is a performance mechanism to avoid having to load very
    highly versioned roots from the event stream. With a snapshot, only the
    events which occur after the snapshot must be loaded. The snapshot frequency
    can be set per-aggregate root and the default frequency is a class property
    of the :class:`recall.repository.Repository`
    """
    def load(self, guid):
        """
        Load an aggregate root from a snapshot

        :param root: The aggregate root
        :rtype: :class:`recall.models.AggregateRoot`
        """
        raise NotImplementedError

    def save(self, root):
        """
        Take a snapshot of an aggregate root

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :type root: :class:`recall.models.AggregateRoot`
        """
        raise NotImplementedError


class Memory(SnapshotStore):
    """
    This snapshot store uses an in-memory :class:`dict` of pickled roots as the
    snapshot store.
    """
    def __init__(self):
        self._snapshots = {}

    def load(self, guid):
        """
        Load an aggregate root from a snapshot

        :param root: The aggregate root
        :rtype: :class:`recall.models.AggregateRoot`
        """
        snapshot = self._snapshots.get(guid)
        return pickle.loads(snapshot) if snapshot else None

    def save(self, entity):
        """
        Take a snapshot of an aggregate root

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :type root: :class:`recall.models.AggregateRoot`
        """
        self._snapshots[entity.guid] = pickle.dumps(entity)