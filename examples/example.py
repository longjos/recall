import yaml

import recall.models
import recall.locators
import recall.event_handler


class CompanyFounded(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class WhenCompanyFounded(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, CompanyFounded)
        self.entity.guid = event['guid']
        self.entity.name = event['name']


class EmployeeHired(recall.models.Event):
    def __init__(self, guid, name, title):
        self._data = {"guid": guid, "name": name, "title": title}


class WhenEmployeeHired(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, EmployeeHired)
        self.entity.guid = event['guid']
        self.entity.name = event['name']
        self.entity.title = event['title']
        self.entity.is_employed = True


class EmployeePromoted(recall.models.Event):
    def __init__(self, guid, title):
        self._data = {"guid": guid, "title": title}


class WhenEmployeePromoted(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, EmployeePromoted)
        self.entity.title = event['title']


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
        self._register_handlers()

    def found(self, command):
        assert isinstance(command, FoundCompany)
        name = command.get("name")
        if name:
            self._apply_event(CompanyFounded(self._create_guid(), name))

    def hire_employee(self, command):
        assert isinstance(command, HireEmployee)
        name = command.get("name")
        title = command.get("title")
        if self.is_founded() and name and title:
            self._apply_event(EmployeeHired(self.guid, name, title))
            employee = Employee()
            employee.hire(command)
            self.employees.add(employee)
            return employee.guid

    def is_founded(self):
        return bool(self.guid)

    def _register_handlers(self):
        self._register_event_handler(CompanyFounded, WhenCompanyFounded)


class Employee(recall.models.Entity):
    def __init__(self):
        super(Employee, self).__init__()
        self.name = None
        self.title = None
        self.is_employed = False
        self._register_handlers()

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

    def _register_handlers(self):
        self._register_event_handler(EmployeeHired, WhenEmployeeHired)
        self._register_event_handler(EmployeePromoted, WhenEmployeePromoted)


def main():
    # Load the settings
    settings = yaml.load(open("config.yml", 'r'))

    # Perform some commands
    company = Company()
    company.found(FoundCompany(name="Planet Express"))
    leela = company.hire_employee(HireEmployee(name="Turanga Leela", title="Captain"))
    fry = company.hire_employee(HireEmployee(name="Philip Fry", title="Delivery Boy"))
    company.employees.get(fry).promote(PromoteEmployee(title="Narwhal Trainer"))

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
