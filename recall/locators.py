import repository
import event_router
import event_store
import snapshot_store


class EventRouterNotFoundError(Exception):
    pass


class EventStoreNotFoundError(Exception):
    pass


class SnapshotStoreNotFoundError(Exception):
    pass


class RepositoryLocator(object):
    DEFAULT_EVENT_STORE = event_store.Memory
    DEFAULT_EVENT_ROUTER = event_router.StdOut
    DEFAULT_SNAPSHOT_STORE = snapshot_store.Memory
    DEFAULT_SNAPSHOT_FREQUENCY = 10

    def __init__(self, settings):
        """
        :type settings: :class:`dict`
        """
        self.settings = settings
        self.identity_map = {}
        self.locator_event_router = EventRouterLocator(settings)
        self.locator_event_store = EventStoreLocator(settings)
        self.locator_snapshot_store = SnapshotStoreLocator(settings)

    def _get_event_router(self, settings):
        cls = settings.get("event_router")
        return (self.locator_event_router.locate(cls)
                if cls else self.DEFAULT_EVENT_ROUTER())

    def _get_event_store(self, settings):
        cls = settings.get("event_store")
        return (self.locator_event_store.locate(cls)
                if cls else self.DEFAULT_EVENT_STORE())

    def _get_snapshot_store(self, settings):
        cls = settings.get("snapshot_store")
        return (self.locator_snapshot_store.locate(cls)
                if cls else self.DEFAULT_SNAPSHOT_STORE())

    def _get_snapshot_frequency(self, settings):
        return (settings.get("snapshot_frequency")
                or self.DEFAULT_SNAPSHOT_FREQUENCY)

    def locate(self, cls):
        """
        :rtype: :class:`recall.repository.Repository`
        """
        fqcn = cls.__module__ + "." + cls.__name__
        if not self.identity_map.get(fqcn):
            settings = self.settings.get(fqcn) or {}
            self.identity_map[fqcn] = repository.Repository(
                cls, self._get_event_store(settings),
                self._get_snapshot_store(settings),
                self._get_event_router(settings),
                self._get_snapshot_frequency(settings))

        return self.identity_map[fqcn]


class EventRouterLocator(object):

    def __init__(self, settings):
        """
        :type settings: :class:`dict`
        """
        self.settings = settings
        self.identity_map = {}

    def locate(self, fqcn):
        """
        :rtype: :class:`recall.event_router.EventRouter`
        """
        if not self.identity_map.get(fqcn):
            class_name = fqcn.split(".")[-1]
            module_name = ".".join(fqcn.split(".")[0:-1])
            mdl = __import__(module_name, globals(), locals(), [class_name], 0)
            if class_name not in dir(mdl):
                raise EventRouterNotFoundError("Could not locate %s" % fqcn)
            cls = getattr(mdl, class_name)
            settings = self.settings.get(fqcn)
            kwargs = settings.get("kwargs") if settings else None
            self.identity_map[fqcn] = cls(**kwargs) if kwargs else cls()

        return self.identity_map[fqcn]


class EventStoreLocator(object):

    def __init__(self, settings):
        """
        :type settings: :class:`dict`
        """
        self.settings = settings
        self.identity_map = {}

    def locate(self, name):
        """
        :rtype: :class:`recall.event_store.EventStore`
        """
        if not self.identity_map.get(name):
            if name not in dir(event_store):
                raise EventStoreNotFoundError("Could not locate %s" % name)
            cls = getattr(event_store, name)
            settings = self.settings.get(name)
            kwargs = settings.get("kwargs") if settings else None
            self.identity_map[name] = cls(**kwargs) if kwargs else cls()

        return self.identity_map[name]


class SnapshotStoreLocator(object):

    def __init__(self, settings):
        """
        :type settings: :class:`dict`
        """
        self.settings = settings
        self.identity_map = {}

    def locate(self, name):
        """
        :rtype: :class:`recall.snapshot_store.SnapshotStore`
        """
        if not self.identity_map.get(name):
            if name not in dir(snapshot_store):
                raise SnapshotStoreNotFoundError("Could not locate %s" % name)
            cls = getattr(snapshot_store, name)
            settings = self.settings.get(name)
            kwargs = settings.get("kwargs") if settings else None
            self.identity_map[name] = cls(**kwargs) if kwargs else cls()

        return self.identity_map[name]