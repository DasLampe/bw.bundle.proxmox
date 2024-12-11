global node
from os.path import dirname, basename

files = {}
actions = {}
directories = {}
downloads = {}
proxmox_users = {}

cfg = node.metadata.get('proxmox')
debian_release_name = node.metadata.get('debian', {}).get('release_name', 'bookworm')

files['/etc/apt/sources.list.d/pve-install-repo.list'] = {
    'content': f'deb [arch=amd64] http://download.proxmox.com/debian/pve {debian_release_name} pve-no-subscription',
    'owner': 'root',
    'group': 'root',
    'mode': '0644',
}

if cfg.get('disable_subscription_note'):
    files['/etc/apt/apt.conf.d/disable-subscription-note-pve'] = {
        'source': 'etc/apt/apt.conf.d/disable-subscription-note-pve',
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
    f'linux-image-{cfg.get("remove_kernel")}-amd64': {
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

# Templates
for template_name, template_conf in cfg.get('template_vms', {}).items():
    downloads[f'/tmp/{basename(template_conf.get('iso_url'))}'] = {
        'url':  template_conf.get('iso_url'),
        'sha256': template_conf.get('iso_sha256'),
        'owner': 'root',
        'group': 'root',
    }

    actions[f'create_proxmox_template_{template_name}'] = {
        'command': f'qm create {template_conf.get("id", 9000)} --name {template_name};'
                   f'qm set {template_conf.get("id", 9000)} --scsi0 {template_conf.get("storage_name", "local")}:0,'
                   f'import-from=/tmp/{basename(template_conf.get("iso_url"))};'
                   f'qm template {template_conf.get("id", 9000)}',
        'needs': [
            f'download:/tmp/{basename(template_conf.get("iso_url"))}',
        ],
        'unless': 'pvesh get /cluster/resources -type vm --output-format yaml | egrep -i "vmid" | '
                  f'cut -d ":" -f2 | tr -d " " | grep -w -q {template_conf.get("id", 9000)}',
    }

# LXC Templates
actions[f'update_lxc_image_list'] = {
    'command': 'pveam update',
}
for image,image_conf in cfg.get('lxc_images', {}).items():
    if image_conf.get('installed', True):
        actions[f'download_lxc_image_{image}'] = {
            'command': f'pveam download {image_conf.get('storage', 'local')} {image}',
            'needs': [
                'action:update_lxc_image_list',
            ],
            #@TODO: Find a way for unless
        }
    else:
        actions[f'remove_lxc_image_{image}'] = {
            'commanmd': f'pveam remove {image_conf.get('storage', 'local')}:{image}'
        }
