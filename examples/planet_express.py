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
    def __init__(self, guid, employee_guid, name, title):
        self._data = {
            "guid": guid,
            "employee_guid": employee_guid,
            "name": name,
            "title": title}


class WhenEmployeeHired(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, EmployeeHired)
        employee = Employee(event['employee_guid'], event['name'], event['title'])
        self.entity.employees.add(employee)


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
            employee = self._create_guid()
            self._apply_event(EmployeeHired(self.guid, employee, name, title))
            return employee

    def is_founded(self):
        return bool(self.guid)

    def _register_handlers(self):
        self._register_event_handler(CompanyFounded, WhenCompanyFounded)
        self._register_event_handler(EmployeeHired, WhenEmployeeHired)


class Employee(recall.models.Entity):
    def __init__(self, guid, name, title):
        super(Employee, self).__init__()
        self.guid = guid
        self.name = name
        self.title = title
        self._register_handlers()

    def promote(self, command):
        assert isinstance(command, PromoteEmployee)
        title = command.get("title")
        if title:
            self._apply_event(EmployeePromoted(self.guid, title))

    def _register_handlers(self):
        self._register_event_handler(EmployeePromoted, WhenEmployeePromoted)


def main():
    # Perform some commands
    company = Company()
    company.found(FoundCompany(name="Planet Express"))
    company.hire_employee(HireEmployee(name="Turanga Leela", title="Captain"))
    fry = company.hire_employee(HireEmployee(name="Philip Fry", title="Delivery Boy"))
    company.employees.get(fry).promote(PromoteEmployee(title="Narwhal Trainer"))

    # Save AR
    repo = recall.locators.RepositoryLocator({}).locate(Company)
    repo.save(company)
    guid = company.guid
    del company

    # Load AR
    company = repo.load(guid)
    print(company.name)
    for employee in company.employees.values():
        print(" - %s, %s" % (employee.name, employee.title))

main()
