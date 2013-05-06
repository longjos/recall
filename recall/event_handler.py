

class DomainEventHandler(object):
    """
    A simple object representing the state change of a domain once an event
    occurs.

    :param entity: The domain entity
    :type entity: :class:`recall.models.Entity`
    """
    def __init__(self, entity):
        self.entity = entity

    def __call__(self, event):
        """
        Handle the domain state change

        :param event: The domain event
        :type event: :class:`recall.models.Event`
        """
        raise NotImplementedError()