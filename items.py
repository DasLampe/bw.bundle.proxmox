from os.path import dirname


files = {}
actions = {}
directories = {}
proxmox_users = {}

cfg = node.metadata.get('proxmox')
debian_release_name = node.metadata.get('debian', {}).get('release_name', 'bookworm')

files['/etc/apt/sources.list.d/pve-install-repo.list'] = {
    'content': f'deb [arch=amd64] http://download.proxmox.com/debian/pve {debian_release_name} pve-no-subscription',
    'owner': 'root',
    'group': 'root',
    'mode': '0644',
}

actions['import_proxmox_gpg_key'] = {
    'command': f'wget https://enterprise.proxmox.com/debian/proxmox-release-{debian_release_name}.gpg '
               f'-O /etc/apt/trusted.gpg.d/proxmox-release-{debian_release_name}.gpg',
    'unless': f'test -f /etc/apt/trusted.gpg.d/proxmox-release-{debian_release_name}.gpg',
    'triggers': [
        'action:force_update_apt_cache',
    ],
}

pkg_apt = {
    'proxmox-default-kernel': {
        'installed': True,
    },
    'proxmox-ve': {
        'installed': True,
    },
    'linux-image-amd64': {
        'installed': False,
    },
    f'linux-image-{cfg.get("installed_kernel")}-amd64': {
        'installed': False,
    },
    'os-prober': {
        'installed': False,
    }
}

for path, content in cfg.get('config_files', {}).items():
    directories[dirname(path)] = {}
    files[path] = {
        'content': content,
        'owner': 'root',
        'group': 'root',
        'mode': '0644',
    }

for user_name, user_conf in cfg.get('users', {}).items():
    proxmox_users[user_name] = {
        'password': user_conf.get('password', repo.vault.password_for(f'proxmox_user_{user_name}_on_{node.name}')),
        'roles': user_conf.get('roles', {}),
        'tokens': user_conf.get('tokens', {}),
    }

# # Create roles
# roles = json.loads(node.run('pveum role list --output-format json').stdout.strip())
# for name, privs in cfg.get('roles', {}).items():
#     if name not in [x.get('roleid') for x in roles]:
#         actions[f'add_role_{name}'] = {
#             'command': f'pveum role add {name} -privs {quote(','.join(privs))}'
#         }
#     elif privs != [x.get('privs') for x in roles if x.get('roleid') == name]:
#         actions[f'adjust_role_privs_{name}'] = {
#             'command': f'pveum role modify {name} -privs {",".join(privs)}'
#         }
#
# # Create users
# act_users = json.loads(node.run('pveum user list --output-format json').stdout.strip())
# for user_name, user_conf in cfg.get('users', {}).items():
#     user_password = user_conf.get("password", repo.vault.password_for(f"proxmox_user_{user_name}_on_{node.name}"))
#     if user_name not in [x.get('userid') for x in act_users]:
#         actions[f'add_user_{user_name}'] = {
#             'command': f'pveum user add {user_name} --password {user_password}',
#         }
#     else:
#         actions[f'set_password_for_user_{user_name}'] = {
#             'command': f'pveum user modify {user_name} --password {user_password}',
#         }
#
#     tokens = [x.get('tokenid') for x in json.loads(node.run(f'pveum user token list {user_name} --output-format json').stdout.strip())]
#     for token, token_conf in user_conf.get('tokens', {}).items():
#         if token not in tokens:
#             act_token = json.loads(node.run(f'pveum user token add {user_name} {token} '
#                                  f'--comment "{token_conf.get("comment", "bundlewrap token")}" '
#                                  f'--privsep {token_conf.get("privsep", 1)} '
#                                  '--output-format json').stdout.strip()).get('value'),
#             token_file = os.path.join(repo.path, 'data', f'proxmox_token_{user_name}')
#             fd = os.open(token_file, os.O_RDWR|os.O_CREAT)
#             os.write(fd, str(act_token).encode('utf-8'))
#             os.close(fd)
#
# # Add ACL
# for acl_conf in cfg.get('acls', []):
#     actions[f'add_acl_{acl_conf.get("path")}_{acl_conf.get("user")}_{acl_conf.get("role")}'] = {
#         'command': f'pveum aclmod {acl_conf.get("path")} -user {acl_conf.get("user")} -role {acl_conf.get("role")}',
#     }
