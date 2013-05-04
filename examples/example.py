import yaml

import recall.models
import recall.locators


class CompanyFounded(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class EmployeeHired(recall.models.Event):
    def __init__(self, guid, name, title):
        self._data = {"guid": guid, "name": name, "title": title}


class EmployeePromoted(recall.models.Event):
    def __init__(self, guid, title):
        self._data = {"guid": guid, "title": title}


class EmployeeTerminated(recall.models.Event):
    def __init__(self, guid, reason):
        self._data = {"guid": guid, "reason": reason}


class EmployeeTerminatedFailed(recall.models.Event):
    pass


class FoundCompany(recall.models.Command):
    pass


class HireEmployee(recall.models.Command):
    pass


class PromoteEmployee(recall.models.Command):
    pass


class TerminateEmployee(recall.models.Command):
    pass


class Company(recall.models.AggregateRoot):
    def __init__(self):
        super(Company, self).__init__()
        self.name = None
        self.employees = recall.models.EntityList()
        self._register_event_handler(CompanyFounded, self._when_founded)

    def found(self, command):
        assert isinstance(command, FoundCompany)
        name = command.get("name")
        if name:
            self._apply_event(CompanyFounded(self._create_guid(), name))

    def hire_employee(self, command):
        assert isinstance(command, HireEmployee)
        name = command.get("name")
        title = command.get("title")
        if name and title:
            self._apply_event(EmployeeHired(self._create_guid(), name, title))
            employee = Employee()
            employee.hire(command)
            self.employees.add(employee)

    def _when_founded(self, event):
        self.guid = event['guid']
        self.name = event['name']


class Employee(recall.models.Entity):
    def __init__(self):
        super(Employee, self).__init__()
        self.name = None
        self.title = None
        self.is_employed = False
        self._register_event_handler(EmployeeHired, self._when_hired)
        self._register_event_handler(EmployeePromoted, self._when_promoted)

    def hire(self, command):
        assert isinstance(command, HireEmployee)
        name = command.get("name")
        title = command.get("title")
        if name and title:
            self._apply_event(EmployeeHired(self._create_guid(), name, title))

    def promote(self, command):
        assert isinstance(command, PromoteEmployee)
        title = command.get("title")
        if self.is_employed and title:
            self._apply_event(EmployeePromoted(self.guid, title))

    def _when_hired(self, event):
        self.guid = event['guid']
        self.name = event['name']
        self.title = event['title']
        self.is_employed = True

    def _when_promoted(self, event):
        self.title = event['title']


def main():
    # Load the settings
    settings = yaml.load(open("config.yml", 'r'))

    # Perform some commands
    company = Company()
    company.found(FoundCompany(name="Planet Express"))
    company.hire_employee(HireEmployee(name="Turanga Leela", title="Captain"))
    company.hire_employee(HireEmployee(name="Philip Fry", title="Delivery Boy"))

    # Save AR
    repo = recall.locators.RepositoryLocator(settings).locate(Company)
    repo.save(company)
    guid = company.guid
    del company

    # Load AR
    company = repo.load(guid)
    print(company.name)
    for employee in company.employees.values():
        print(" - %s, %s" % (employee.name, employee.title))

main()
