import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
import optparse
import random
import uuid

import yaml

import recall.event_handler
import recall.models
import recall.locators

accounts = []
accounts_with_campaigns = []
accounts_with_campaigns_with_mailings = []
counts = {}


class CreateAccount(recall.models.Command):
    pass


class ChangeAccountName(recall.models.Command):
    pass


class ChangeCampaignName(recall.models.Command):
    pass


class AddAccountMember(recall.models.Command):
    pass


class AddAccountCampaign(recall.models.Command):
    pass


class SendCampaignMailing(recall.models.Command):
    pass


class OpenMailing(recall.models.Command):
    pass


class ClickMailing(recall.models.Command):
    pass


class ShareMailing(recall.models.Command):
    pass


class AccountCreated(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class AccountNameChanged(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class CampaignNameChanged(recall.models.Event):
    def __init__(self, guid, name):
        self._data = {"guid": guid, "name": name}


class AccountMemberAdded(recall.models.Event):
    def __init__(self, guid, address):
        self._data = {"guid": guid, "address": address}


class AccountCampaignAdded(recall.models.Event):
    def __init__(self, guid, campaign_guid, name):
        self._data = {"guid": guid, "campaign_guid": campaign_guid, "name": name}


class CampaignMailingSent(recall.models.Event):
    def __init__(self, guid, mailing_guid, name):
        self._data = {"guid": guid, "mailing_guid": mailing_guid, "name": name}


class MailingOpened(recall.models.Event):
    def __init__(self, guid, datetime, address):
        self._data = {"guid": guid, "datetime": datetime, "address": address}


class MailingClicked(recall.models.Event):
    def __init__(self, guid, datetime, address):
        self._data = {"guid": guid, "datetime": datetime, "address": address}


class MailingShared(recall.models.Event):
    def __init__(self, guid, datetime, address):
        self._data = {"guid": guid, "datetime": datetime, "address": address}


class WhenAccountCreated(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountCreated)
        self.entity.guid = event['guid']
        self.entity.name = event['name']


class WhenAccountNameChanged(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountNameChanged)
        self.entity.name = event['name']


class WhenCampaignNameChanged(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, CampaignNameChanged)
        self.entity.name = event['name']


class WhenAccountMemberAdded(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountMemberAdded)
        self.entity.members.append(event['address'])


class WhenAccountCampaignAdded(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, AccountCampaignAdded)
        campaign = Campaign(event["campaign_guid"], event["name"])
        self.entity.campaigns.add(campaign)


class WhenCampaignMailingSent(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, CampaignMailingSent)
        mailing = Mailing(event["mailing_guid"], event["name"])
        self.entity.mailings.add(mailing)


class WhenMailingOpened(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, MailingOpened)
        if event["address"] not in self.entity.engaged:
            self.entity.engaged.append(event["address"])


class WhenMailingClicked(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, MailingClicked)
        if event["address"] not in self.entity.engaged:
            self.entity.engaged.append(event["address"])


class WhenMailingShared(recall.event_handler.DomainEventHandler):
    def __call__(self, event):
        assert isinstance(event, MailingShared)
        if event["address"] not in self.entity.engaged:
            self.entity.engaged.append(event["address"])


class Account(recall.models.AggregateRoot):
    def __init__(self):
        super(Account, self).__init__()
        self.name = None
        self.members = []
        self.campaigns = recall.models.EntityList()
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

    def add_campaign(self, command):
        assert isinstance(command, AddAccountCampaign)
        name = command.get("name")
        if self.is_created() and name:
            campaign = self._create_guid()
            self._apply_event(AccountCampaignAdded(self.guid, campaign, name))

    def _register_handlers(self):
        self._register_event_handler(AccountCreated, WhenAccountCreated)
        self._register_event_handler(AccountNameChanged, WhenAccountNameChanged)
        self._register_event_handler(AccountMemberAdded, WhenAccountMemberAdded)
        self._register_event_handler(AccountCampaignAdded, WhenAccountCampaignAdded)


class Campaign(recall.models.Entity):
    def __init__(self, guid, name):
        super(Campaign, self).__init__()
        self.guid = guid
        self.name = name
        self.mailings = recall.models.EntityList()
        self._register_handlers()

    def change_name(self, command):
        assert isinstance(command, ChangeCampaignName)
        name = command.get("name")
        if name:
            self._apply_event(CampaignNameChanged(self.guid, name))

    def send_mailing(self, command):
        assert isinstance(command, SendCampaignMailing)
        name = command.get("name")
        if name:
            mailing = self._create_guid()
            self._apply_event(CampaignMailingSent(self.guid, mailing, name))

    def _register_handlers(self):
        self._register_event_handler(CampaignNameChanged, WhenCampaignNameChanged)
        self._register_event_handler(CampaignMailingSent, WhenCampaignMailingSent)


class Mailing(recall.models.Entity):
    def __init__(self, guid, name):
        super(Mailing, self).__init__()
        self.guid = guid
        self.name = name
        self.engaged = []
        self._register_handlers()

    def open(self, command):
        assert isinstance(command, OpenMailing)
        address = command.get("address")
        datetime = command.get("datetime")
        if address and datetime:
            self._apply_event(MailingOpened(self.guid, datetime, address))

    def click(self, command):
        assert isinstance(command, ClickMailing)
        address = command.get("address")
        datetime = command.get("datetime")
        if address and datetime:
            self._apply_event(MailingClicked(self.guid, datetime, address))

    def share(self, command):
        assert isinstance(command, ShareMailing)
        address = command.get("address")
        datetime = command.get("datetime")
        if address and datetime:
            self._apply_event(MailingShared(self.guid, datetime, address))

    def _register_handlers(self):
        self._register_event_handler(MailingOpened, WhenMailingOpened)
        self._register_event_handler(MailingClicked, WhenMailingClicked)
        self._register_event_handler(MailingShared, WhenMailingShared)


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
        account = repo.load(random.choice(accounts))
        account.add_campaign(AddAccountCampaign(name="Foo %s" % random.randint(100, 999)))
        repo.save(account)
        accounts_with_campaigns.append(account.guid)


def exec_change_campaign_name(repo):
    if accounts_with_campaigns and counts.get('CampaignCreated', 0) < 10:
        counts['CampaignUpdated'] = counts.get('CampaignUpdated', 0) + 1
        account = repo.load(random.choice(accounts_with_campaigns))
        campaign = random.choice(account.campaigns.values())
        campaign.change_name(ChangeCampaignName(name="Foo %s" % random.randint(100, 999)))
        repo.save(account)


def exec_send_mailing(repo):
    if accounts_with_campaigns and counts.get('MailingCreated', 0) < 1000:
        counts['MailingCreated'] = counts.get('MailingCreated', 0) + 1
        account = repo.load(random.choice(accounts_with_campaigns))
        campaign = random.choice(account.campaigns.values())
        campaign.send_mailing(SendCampaignMailing(name="Foo %s" % random.randint(1000, 9999)))
        repo.save(account)
        accounts_with_campaigns_with_mailings.append((account.guid, campaign.guid))


def exec_open_mailing(repo):
    if accounts_with_campaigns_with_mailings:
        counts['MailingOpened'] = counts.get('MailingOpened', 0) + 1
        account_guid, campaign_guid = random.choice(accounts_with_campaigns_with_mailings)
        account = repo.load(account_guid)
        campaign = account.campaigns[campaign_guid]
        mailing = random.choice(campaign.mailings.values())
        mailing.open(OpenMailing(datetime=random_time(), address=random_address()))
        repo.save(account)


def exec_click_mailing(repo):
    if accounts_with_campaigns_with_mailings:
        counts['MailingClicked'] = counts.get('MailingClicked', 0) + 1
        account_guid, campaign_guid = random.choice(accounts_with_campaigns_with_mailings)
        account = repo.load(account_guid)
        campaign = account.campaigns[campaign_guid]
        mailing = random.choice(campaign.mailings.values())
        mailing.click(ClickMailing(datetime=random_time(), address=random_address()))
        repo.save(account)


def exec_share_mailing(repo):
    if accounts_with_campaigns_with_mailings:
        counts['MailingShared'] = counts.get('MailingShared', 0) + 1
        account_guid, campaign_guid = random.choice(accounts_with_campaigns_with_mailings)
        account = repo.load(account_guid)
        campaign = account.campaigns[campaign_guid]
        mailing = random.choice(campaign.mailings.values())
        mailing.share(ShareMailing(datetime=random_time(), address=random_address()))
        repo.save(account)


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
    settings = yaml.load(open("examples/config.yml", 'r'))
    values, args = parse_cli_options()
    count = values.count
    repo = recall.locators.RepositoryLocator(settings).locate(Account)

    print("%s started at %s\n" % (name, datetime.datetime.now().isoformat()))

    for i in range(0, count):
        random_exec(repo)

    print("New Accounts: %s (with %s updates)" % (counts.get('AccountCreated', 0), counts.get('AccountUpdated', 0)))
    print("New Campaigns: %s (with %s updates)" % (counts.get('CampaignCreated', 0), counts.get('CampaignUpdated', 0)))
    print("New Mailings: %s (with %s updates)" % (counts.get('MailingCreated', 0), counts.get('MailingUpdated', 0)))
    print("New Addresses: %s" % counts.get('AddressCreated', 0))
    print("")
    print("Opens: %s" % counts.get('MailingOpened', 0))
    print("Clicks: %s" % counts.get('MailingClicked', 0))
    print("Shares: %s" % counts.get('MailingShared', 0))
    print("Bounces: %s" % counts.get('MailingBounced', 0))
    print("")
    print("total: %s" % reduce(lambda x, y: x + y, counts.values(), 0))

    print("\n%s stopped at %s\n\n" % (name, datetime.datetime.now().isoformat()))

main()
