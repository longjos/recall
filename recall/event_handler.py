

class DomainEventHandler(object):
    def __init__(self, entity):
        self.entity = entity

    def __call__(self, event):
        raise NotImplementedError()