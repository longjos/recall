import collections
import uuid

import recall.event_store
import recall.event_router
import recall.models
import recall.snapshot_store


class Repository(object):
    """
    The repository supports interacting with domain objects in a way which
    mimics the memento pattern. The pattern isn't as important as the fact that
    the repository will always give you the aggregate root at it's latest
    version. It does this by first trying to load from an in-memory identity
    map, then from a snapshot, and lastly from the event stream.

    Saving works much the same way, but in reverse. First all staged events are
    stored in the event stream, then those events are routed (if necessary), and
    then a snapshot is taken (if needed).

    :param root_cls: The class object of the Aggregate Root
    :type root_cls: :class:`type`

    :param event_store: The event store
    :type event_store: :class:`recall.event_store.EventStore`

    :param snapshot_store: The snapshot store
    :type snapshot_store: :class:`recall.snapshot_store.SnapshotStore`

    :param event_router: The event router
    :type event_router: :class:`recall.event_router.EventRouter`

    :param snapshot_frequency: The snapshot frequency
    :type snapshot_frequency: :class:`int`
    """
    def __init__(self, root_cls, event_store, snapshot_store, event_router,
                 snapshot_frequency):
        assert isinstance(root_cls, type)
        assert isinstance(event_store, recall.event_store.EventStore)
        assert isinstance(snapshot_store, recall.snapshot_store.SnapshotStore)
        assert isinstance(event_router, recall.event_router.EventRouter)
        assert isinstance(snapshot_frequency, int)
        self.identity_map = {}
        self.root_cls = root_cls
        self.event_store = event_store
        self.snapshot_store = snapshot_store
        self.event_router = event_router
        self.snapshot_frequency = snapshot_frequency

    def load(self, guid):
        """
        Get an aggregate root by GUID

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(guid, uuid.UUID)
        root = self._load_entity(guid)
        self._update_children(root)
        return root

    def save(self, root):
        """
        Save an aggregate root

        :param root: The aggregate root
        :type root: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(root, recall.models.AggregateRoot)
        if not root.get_all_events():
            return

        self.event_store.save(root)
        self._route_all_events(root)
        self._clean_entity(root)
        if root._version % self.snapshot_frequency == 0:
            self.snapshot_store.save(root)

    def _clean_entity(self, root):
        """
        Clears staged events and increments versions on all entities in the
        aggregate.

        :param root: The aggregate root
        :type root: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(root, recall.models.AggregateRoot)
        for entity in root._get_all_entities():
            entity._increment_version(len(entity._events))
            entity._clear_events()

    def _route_all_events(self, root):
        """
        Routes all staged events for all entities in the aggregate.

        :param root: The aggregate root
        :type root: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(root, recall.models.AggregateRoot)
        for event in root.get_all_events():
            self.event_router.route(event)

    def _load_entity(self, guid):
        """
        Get an aggregate root by GUID

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(guid, uuid.UUID)
        entity = (
            self._load_from_identity_map(guid)
            or self._load_from_snapshot(guid)
            or self._load_from_event_store(guid)
        )

        if entity:
            self.identity_map[entity.guid] = entity

        return entity

    def _load_from_identity_map(self, guid):
        """
        Attempt to get an aggregate root by GUID from the identity map

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(guid, uuid.UUID)
        return self.identity_map.get(guid)

    def _load_from_snapshot(self, guid):
        """
        Attempt to get an aggregate root by GUID from a snapshot

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(guid, uuid.UUID)
        entity = self.snapshot_store.load(guid)

        if entity:
            events = self.event_store.get_events_from_version(guid, entity._version)
            self._push_events(entity, events)

        return entity

    def _load_from_event_store(self, guid):
        """
        Attempt to get an aggregate root by GUID from the event stream

        :param guid: The guid of the aggregate root
        :type guid: :class:`uuid.UUID`

        :rtype: :class:`recall.models.AggregateRoot`
        """
        assert isinstance(guid, uuid.UUID)
        ar = self.root_cls()
        events = self.event_store.get_all_events(guid)
        self._push_events(ar, events)
        return ar

    def _update_children(self, entity):
        """
        Updates all children on a domain entity to their current version.

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`
        """
        assert isinstance(entity, recall.models.Entity)
        for child in entity._get_child_entities():
            self._push_events(child, self.event_store.get_events_from_version(
                child.guid,
                child._version))
            self._update_children(child)

    def _push_events(self, entity, events):
        """
        Updates a single domain entity to its current version.

        :param entity: The domain entity
        :type entity: :class:`recall.models.Entity`

        :param events: The domain events
        :type events: :class:`collections.Iterable`
        """
        assert isinstance(entity, recall.models.Entity)
        assert isinstance(events, collections.Iterable)
        for event in events:
            entity._handle_domain_event(event)
            entity._increment_version()
