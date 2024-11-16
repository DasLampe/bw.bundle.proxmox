defaults = {
    'apt': {
        'packages': {
            'ca-certificates': {},
            'apt-transport-https': {},
        }
    },
    'proxmox': {
        'remove_kernel': '6.1.0-0',
        'disable_subscription_note': False,
        'users': {
            #'terraform@pve': {
            #    'roles': {
            #        'Terraform': {
            #            'privs': [
            #                'Datastore.AllocateSpace',
            #            ],
            #        },
            #    },
            #    'tokens': {
            #        'tf-provider': {
            #            'comment': 'Terraform API Key for VM management',
            #            'privsep': 0,
            #        }
            #    }
            #},
        },
        'config_files': {
            #'/var/lib/vz/snippets/ci-user.yml': '...'
        },
        'template_vms': {
            #'debian12-cloudinit': {
            #    'id': '9000',
            #    'iso_url': 'https://cloud.debian.org/images/cloud/bookworm/20241110-1927/debian-12-genericcloud-amd64-20241110-1927.qcow2',
            #    'iso_sha256': '1c2452019a76a7f1d0e958d03278a2ba306f51b5b2b8821b26b59d55120440a7',
            #}
        },
    }
}
