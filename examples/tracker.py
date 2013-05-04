import datetime
import logging
import optparse
import random
import uuid

import yaml

import recall.event_handler
import recall.models
import recall.locators

accounts = []
campaign_identity_map = {}
mailing_identity_map = {}
counts = {}


def publish_MailingOpened():
    if address_identity_map and mailing_identity_map:
        counts['MailingOpened'] = counts.get('MailingOpened', 0) + 1
        return rep.messages.MailingOpened(
            random.choice(tuple(address_identity_map.keys())),
            random.choice(tuple(mailing_identity_map.keys())),
            random_time()
        )


def publish_MailingClicked():
    if address_identity_map and mailing_identity_map:
        counts['MailingClicked'] = counts.get('MailingClicked', 0) + 1
        return rep.messages.MailingClicked(
            random.choice(tuple(address_identity_map.keys())),
            random.choice(tuple(mailing_identity_map.keys())),
            random_time()
        )


def publish_MailingShared():
    if address_identity_map and mailing_identity_map:
        counts['MailingShared'] = counts.get('MailingShared', 0) + 1
        return rep.messages.MailingShared(
            random.choice(tuple(address_identity_map.keys())),
            random.choice(tuple(mailing_identity_map.keys())),
            random_time()
        )


def publish_MailingBounced():
    if address_identity_map and mailing_identity_map:
        counts['MailingBounced'] = counts.get('MailingBounced', 0) + 1
        return rep.messages.MailingBounced(
            random.choice(tuple(address_identity_map.keys())),
            random.choice(tuple(mailing_identity_map.keys())),
            random_time()
        )


def publish_MailingCreated():
    if campaign_identity_map and len(mailing_identity_map) < 1000:
        counts['MailingCreated'] = counts.get('MailingCreated', 0) + 1
        ref_mailing_id = random.randint(1000, 9999)
        while ref_mailing_id in mailing_identity_map:
            ref_mailing_id = random.randint(1000, 9999)
        mailing_identity_map[ref_mailing_id] = {
            'ref_campaign_id': random.choice(tuple(campaign_identity_map.keys())),
            'ref_mailing_id': ref_mailing_id,
            'ref_mailing_name': "Mailing (%s)" % significant()
        }
        return rep.messages.MailingCreated(**mailing_identity_map[ref_mailing_id])


def publish_MailingUpdated():
    if mailing_identity_map and counts.get('MailingUpdated', 0) < 10:
        counts['MailingUpdated'] = counts.get('MailingUpdated', 0) + 1
        mailing = random.choice(tuple(mailing_identity_map.values()))
        mailing['ref_mailing_name'] = "Mailing (%s)" % significant()
        return rep.messages.MailingUpdated(**mailing)


class CreateAccount(recall.models.Command):
    pass


class ChangeAccountName(recall.models.Command):
    pass


class AddAccountMember(recall.models.Command):
    pass


class AccountCreated(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class AccountNameChanged(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class AccountMemberAdded(recall.models.Event):
    def __init__(self, guid, address):
        self._data = {"guid": guid, "address": address}


class WhenAccountCreated(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountCreated)
        self.entity.guid = event['guid']
        self.entity.name = event['name']


class WhenAccountNameChanged(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountNameChanged)
        self.entity.guid = event['guid']
        self.entity.name = event['name']


class WhenAccountMemberAdded(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountMemberAdded)
        self.entity.members.append(event['address'])


class Account(recall.models.AggregateRoot):
    def __init__(self):
        super(Account, self).__init__()
        self.name = None
        self.members = []
        self._register_handlers()

    def is_created(self):
        return bool(self.guid)

    def create(self, command):
        assert isinstance(command, CreateAccount)
        name = command.get("name")
        if not self.is_created() and name:
            self._apply_event(AccountCreated(self._create_guid(), name))

    def change_name(self, command):
        assert isinstance(command, ChangeAccountName)
        name = command.get("name")
        if self.is_created() and name:
            self._apply_event(AccountNameChanged(self.guid, name))

    def add_member(self, command):
        assert isinstance(command, AddAccountMember)
        address = command.get("address")
        if self.is_created() and address:
            self._apply_event(AccountMemberAdded(self.guid, address))

    def _register_handlers(self):
        self._register_event_handler(AccountCreated, WhenAccountCreated)
        self._register_event_handler(AccountNameChanged, WhenAccountNameChanged)
        self._register_event_handler(AccountMemberAdded, WhenAccountMemberAdded)


class Campaign(recall.models.Entity):
    def __init__(self):
        super(Account, self).__init__()
        self.name = None
        self.mailings = recall.models.EntityList()
        self._register_handlers()

    def is_created(self):
        return bool(self.guid)

    def create(self, command):
        assert isinstance(command, CreateCampaign)
        name = command.get("name")
        if not self.is_created() and name:
            self._apply_event(CampaignCreated(self._create_guid(), name))

    def change_name(self, command):
        assert isinstance(command, ChangeCampaignName)
        name = command.get("name")
        if self.is_created() and name:
            self._apply_event(CampaignNameChanged(self.guid, name))

    def create_mailing(self, command):
        assert isinstance(command, AddAccountMember)
        address = command.get("address")
        if self.is_created() and address:
            self._apply_event(AccountMemberAdded(self.guid, address))

    def _register_handlers(self):
        self._register_event_handler(CampaignCreated, WhenCampaignCreated)
        self._register_event_handler(CampaignNameChanged, WhenCampaignNameChanged)
        self._register_event_handler(MailingCreated, WhenMailingCreated)


def exec_create_account(repo):
    if counts.get('AccountCreated', 0) < 10:
        counts['AccountCreated'] = counts.get('AccountCreated', 0) + 1
        account = Account()
        account.create(CreateAccount(name="Foo %s" % random.randint(10, 99)))
        repo.save(account)
        accounts.append(account.guid)


def exec_change_account_name(repo):
    if accounts and counts.get('AccountUpdated', 0) < 10:
        counts['AccountUpdated'] = counts.get('AccountUpdated', 0) + 1
        account = repo.load(random.choice(accounts))
        account.change_name(ChangeAccountName(name="Foo %s" % random.randint(10, 99)))
        repo.save(account)


def exec_create_address(repo):
    if accounts:
        counts['AddressCreated'] = counts.get('AddressCreated', 0) + 1
        account = repo.load(random.choice(accounts))
        account.add_member(AddAccountMember(address=random_address()))
        repo.save(account)


def exec_create_campaign(repo):
    if accounts and counts.get('CampaignCreated', 0) < 100:
        counts['CampaignCreated'] = counts.get('CampaignCreated', 0) + 1
        ref_campaign_id = random.randint(100, 999)
        while ref_campaign_id in campaign_identity_map:
            ref_campaign_id = random.randint(100, 999)
        campaign_identity_map[ref_campaign_id] = {
            'ref_account_id': random.choice(tuple(account_identity_map.keys())),
            'ref_campaign_id': ref_campaign_id,
            'ref_campaign_name': "Campaign (%s)" % significant()
        }
        return rep.messages.CampaignCreated(**campaign_identity_map[ref_campaign_id])


def exec_change_campaign_name(repo):
    if campaign_identity_map and counts.get('CampaignCreated', 0) < 10:
        counts['CampaignUpdated'] = counts.get('CampaignUpdated', 0) + 1
        campaign = random.choice(tuple(campaign_identity_map.values()))
        campaign['ref_campaign_name'] = "Campaign (%s)" % significant()
        return rep.messages.CampaignUpdated(**campaign)


def random_address():
    return "test+%s@example.com" % str(uuid.uuid4())


def random_time():
    return (datetime.datetime.now()
            - datetime.timedelta(seconds=random.randint(0, 157680000)))


def random_exec(repo):
    return globals()[random.choice([p for p in globals() if p[:5] == "exec_"])](repo)


def parse_cli_options():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--count", dest="count", default=100, type="int",
                      help="Count of random events to generate")

    return parser.parse_args()


def main():
    name = "Tracker Demo"
    settings = yaml.load(open("config.yml", 'r'))
    values, args = parse_cli_options()
    count = values.count
    repo = recall.locators.RepositoryLocator(settings).locate(Account)

    print("%s started at %s\n" % (name, datetime.datetime.now().isoformat()))

    for i in range(0, count):
        random_exec(repo)

    print("\n%s stopped at %s\n\n" % (name, datetime.datetime.now().isoformat()))

main()
