

class AggregateRootNotFound(Exception):
    pass


class Repository(object):

    def __init__(self, root_class, event_store, snapshot_store, event_router,
                 snapshot_frequency):
        self.identity_map = {}
        self.root_class = root_class
        self.event_store = event_store
        self.snapshot_store = snapshot_store
        self.event_router = event_router
        self.snapshot_frequency = snapshot_frequency

    def load(self, guid):
        root = self._load_entity(guid)

        for child in root._get_child_entities():
            ver = child._version + 1
            events = self.event_store.get_events_from_version(guid, ver)
            self._push_events(child, events)

        return root

    def save(self, root):
        """
        :type root: :class:`recall.models.Entity`
        """
        if not root._get_all_events():
            return

        self.event_store.save(root)
        self._route_all_events(root)
        self._clean_entity(root)
        self.snapshot_store.save(root)

    def _clean_entity(self, root):
        for entity in root._get_all_entities():
            entity._increment_version(len(entity._events))
            entity._clear_events()

    def _route_all_events(self, root):
        for event in root._get_all_events():
            self.event_router.route(event)

    def _load_entity(self, guid):
        entity = (
            self._load_from_identity_map(guid)
            or self._load_from_snapshot(guid)
            or self._load_from_event_store(guid)
        )

        if not entity:
            return

        self.identity_map[entity.guid] = entity
        return entity

    def _load_from_identity_map(self, guid):
        return self.identity_map.get(guid)

    def _load_from_snapshot(self, guid):
        entity = self.snapshot_store.load(guid)

        if entity:
            ver = entity._version + 1
            events = self.event_store.get_events_from_version(guid, ver)
            self._push_events(entity, events)

        return entity

    def _load_from_event_store(self, guid):
        entity_cls = self.event_store.get_type(guid)

        if entity_cls:
            entity = entity_cls()
            events = self.event_store.get_all_events(guid)
            self._push_events(entity, events)
            return entity

    def _push_events(self, entity, events):
        for event in events:
            entity._handle_domain_event(event)
            entity._increment_version()
