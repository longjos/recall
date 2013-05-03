import yaml

import cqrs.models
import cqrs.locators


class EmployeeHired(cqrs.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class EmployeeTrained(cqrs.models.Event):
    pass


class EmployeeTerminated(cqrs.models.Event):
    def __init__(self, guid, reason):
        self._data = {"guid": guid, "reason": reason}


class EmployeeTerminatedFailed(cqrs.models.Event):
    pass


class HireEmployee(cqrs.models.Command):
    pass


class TrainEmployee(cqrs.models.Command):
    pass


class TerminateEmployee(cqrs.models.Command):
    pass


class Employee(cqrs.models.AggregateRoot):
    def __init__(self):
        super(Employee, self).__init__()
        self.name = None
        self.is_employed = False
        self.is_trained = False
        self._register_event_handler(HireEmployee, self._handle_EmployeeHired)
        self._register_event_handler(TrainEmployee, self._handle_EmployeeTrained)
        self._register_event_handler(TerminateEmployee, self._handle_EmployeeTerminated)

    def hire(self, command):
        assert isinstance(command, HireEmployee)
        name = command.get("name")
        if name:
            self._apply_event(EmployeeHired(
                self._create_guid(),
                name
            ))

    def train(self, command):
        assert isinstance(command, TrainEmployee)
        if self.is_employed:
            self._apply_event(EmployeeTrained(self.guid))

    def terminate(self, command):
        assert isinstance(command, TerminateEmployee)
        reason = command.get("reason")
        if self.is_employed and reason:
            self._apply_event(EmployeeTerminated(self.guid, reason))
        else:
            self._apply_event(EmployeeTerminatedFailed(self.guid))

    def _handle_EmployeeHired(self, event):
        self.guid = event['guid']
        self.name = event['name']
        self.is_employed = True

    def _handle_EmployeeTrained(self, event):
        self.is_trained = True

    def _handle_EmployeeTerminated(self, event):
        self.is_employed = False


def main():
    # Load the settings
    settings = yaml.load(open("config.yml", 'r'))

    # Perform some commands
    emp1 = Employee()
    emp1.hire(HireEmployee(name="Fry"))
    emp1.train(TrainEmployee())
    emp1.terminate(TerminateEmployee(reason="Not likeable"))

    # Save AR
    repo = cqrs.locators.RepositoryLocator(settings).locate(Employee)
    repo.save(emp1)
    guid = emp1.guid
    del emp1

    # Load AR
    emp2 = repo.load(guid)
    emp2.terminate(TerminateEmployee(reason="Theft"))
    repo.save(emp2)

main()
