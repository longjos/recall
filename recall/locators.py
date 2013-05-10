import recall.event_router
import recall.event_store
import recall.models
import recall.repository
import recall.snapshot_store


class ServiceNotFoundError(Exception):
    pass


class RepositoryLocator(object):
    """
    A service locator for Repositories:

    :param settings: The configuration settings
    :type settings: :class:`dict`
    """
    DEFAULT_EVENT_STORE = recall.event_store.Memory
    DEFAULT_EVENT_ROUTER = recall.event_router.StdOut
    DEFAULT_SNAPSHOT_STORE = recall.snapshot_store.Memory
    DEFAULT_SNAPSHOT_FREQUENCY = 10

    def __init__(self, settings):
        assert isinstance(settings, dict)
        self.settings = settings
        self.identity_map = {}
        self.locator_event_router = Locator(settings)
        self.locator_event_store = Locator(settings)
        self.locator_snapshot_store = Locator(settings)

    def _get_event_router(self, settings):
        """
        Locate an event router, or use default

        :param settings: The configuration settings
        :type settings: :class:`dict`

        :rtype: :class:`recall.event_router.EventRouter`
        """
        assert isinstance(settings, dict)
        cls = settings.get("event_router")
        return (self.locator_event_router.locate(cls)
                if cls else self.DEFAULT_EVENT_ROUTER())

    def _get_event_store(self, settings):
        """
        Locate an event store, or use default

        :param settings: The configuration settings
        :type settings: :class:`dict`

        :rtype: :class:`recall.event_store.EventStore`
        """
        assert isinstance(settings, dict)
        cls = settings.get("event_store")
        return (self.locator_event_store.locate(cls)
                if cls else self.DEFAULT_EVENT_STORE())

    def _get_snapshot_store(self, settings):
        """
        Locate a snapshot store, or use default

        :param settings: The configuration settings
        :type settings: :class:`dict`

        :rtype: :class:`recall.snapshot_store.SnapshotStore`
        """
        assert isinstance(settings, dict)
        cls = settings.get("snapshot_store")
        return (self.locator_snapshot_store.locate(cls)
                if cls else self.DEFAULT_SNAPSHOT_STORE())

    def _get_snapshot_frequency(self, settings):
        """
        Get the snapshot frequency, or use default

        :param settings: The configuration settings
        :type settings: :class:`dict`

        :rtype: :class:`int`
        """
        assert isinstance(settings, dict)
        return (settings.get("snapshot_frequency")
                or self.DEFAULT_SNAPSHOT_FREQUENCY)

    def locate(self, ar_cls):
        """
        Load a repository for given aggregate root by its fully-qualified class
        name (fqcn). Each AR's repository can be configured with it's own event
        store, snapshot store, event router, and frequency.

        :param ar_cls: The Aggregate Root class
        :type ar_cls: :class:`type`

        :rtype: :class:`recall.repository.Repository`
        """
        assert isinstance(ar_cls, type(recall.models.AggregateRoot))
        fqcn = ar_cls.__module__ + "." + ar_cls.__name__
        if not self.identity_map.get(fqcn):
            settings = self.settings.get(fqcn) or {}
            self.identity_map[fqcn] = recall.repository.Repository(
                ar_cls, self._get_event_store(settings),
                self._get_snapshot_store(settings),
                self._get_event_router(settings),
                self._get_snapshot_frequency(settings))

        return self.identity_map[fqcn]


class Locator(object):
    """
    A simple service locator

    :param settings: The configuration settings
    :type settings: :class:`dict`
    """
    def __init__(self, settings):
        assert isinstance(settings, dict)
        self.settings = settings
        self.identity_map = {}

    def locate(self, fqcn):
        """
        Load a service by its fully-qualified class name (fqcn)

        :param fqcn: The fully-qualified class name of the service
        :type fqcn: :class:`str`

        :rtype: :class:`object`
        """
        assert isinstance(fqcn, str)
        if not self.identity_map.get(fqcn):
            class_name = fqcn.split(".")[-1]
            module_name = ".".join(fqcn.split(".")[0:-1])
            mdl = __import__(module_name, globals(), locals(), [class_name], 0)
            if class_name not in dir(mdl):
                raise ServiceNotFoundError("Could not locate %s" % fqcn)
            cls = getattr(mdl, class_name)
            settings = self.settings.get(fqcn)
            self.identity_map[fqcn] = cls(**settings) if settings else cls()

        return self.identity_map[fqcn]