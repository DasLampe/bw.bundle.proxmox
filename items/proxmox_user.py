import json
import os

from bundlewrap.items import Item
from bundlewrap.exceptions import RemoteException

class ProxmoxUsers(Item):
    """
    Manage Proxmox Users, Roles and Tokens
    """
    BUNDLE_ATTRIBUTE_NAME = 'proxmox_users'
    NEEDS_STATIC = [
        "pkg_apt:",
        "pkg_pacman:",
        "pkg_yum:",
        "pkg_zypper:",
    ]
    ITEM_ATTRIBUTES = {
        'password': None,
        'roles': {},
        'tokens': {},
    }
    ITEM_TYPE_NAME = 'proxmox_user'
    REQUIRED_ATTRIBUTES = [
        'password',
    ]

    def get_username(self):
        return self.name

    @classmethod
    def block_concurrent(cls, node_os, node_os_version):
        """
        Return a list of item types that cannot be applied in parallel
        with this item type.
        """
        return []

    def __repr__(self):
        return f"<Proxmox User username:{self.get_username()}>"

    def cdict(self):
        return {
            'user exist': True,
            'roles': set([k for k in self.attributes.get('roles', {}).keys()]),
            'tokens': set([k for k in self.attributes.get('tokens', {}).keys()]),
            'missing acl': False,
        }

    def sdict(self):
        try:
            users = json.loads(self.node.run('pveum user list --output-format json').stdout.strip())
            roles = json.loads(self.node.run('pveum role list --output-format json').stdout.strip())
            tokens = []
            if self.get_username() in [x.get('userid') for x in users if x.get('userid') == self.get_username()]:
                tokens = json.loads(self.node.run(f'pveum user token list {self.get_username()} --output-format json').stdout.strip())
        except RemoteException:
            users = []
            roles = []
            tokens = []
        acls = json.loads(self.node.run('pveum acl list --output-format json').stdout.strip())

        requested_roles = set([key for key in self.attributes.get("roles").keys()])
        requested_tokens = set([key for key in self.attributes.get('tokens').keys()])
        user_acls = [u for u in acls if u.get('ugid') == self.get_username()]

        return {
            'user exist': self.get_username() in [x.get('userid') for x in users],
            'roles': requested_roles.intersection([x.get('roleid') for x in roles]),
            'tokens': requested_tokens.intersection([x.get('tokenid') for x in tokens]),
            'missing acl': not set(requested_roles.difference([x.get('roleid') for x in user_acls])) == set(),
        }

    def fix(self, status):
        username = self.get_username()

        if not status.sdict.get('user exist'):
            self.node.run(f'pveum user add {username} --password {self.attributes.get("password")}')

        for role_name, role_conf in self.attributes.get('roles').items():
            if role_name not in status.sdict.get('roles'):
                self.node.run(f'pveum role add {role_name} -privs "{",".join(role_conf.get("privs"))}"')

        for token_name, token_conf in self.attributes.get('tokens').items():
            if token_name not in status.sdict.get('tokens'):
                 act_token = json.loads(self.node.run(f'pveum user token add {username} {token_name} '
                                      f'--comment "{token_conf.get("comment", "bundlewrap token")}" '
                                      f'--privsep {token_conf.get("privsep", 1)} '
                                      '--output-format json').stdout.strip()).get('value'),
                 token_file = os.path.join(self.node.repo.path, 'data', f'proxmox_token_{username}!{token_name}')
                 fd = os.open(token_file, os.O_RDWR|os.O_CREAT)
                 os.write(fd, str(act_token).encode('utf-8'))
                 os.close(fd)

        if status.sdict.get('missing acl'):
            for role_name in self.attributes.get('roles').keys():
               self.node.run(f'pveum aclmod / -user {username} -role {role_name}')

        #@TODO: Privileges check; removal of tokens, etc.
