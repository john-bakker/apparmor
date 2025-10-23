# Ansible Collection - exo.apparmor

This collection contains utilities and modules for managing AppArmor configurations.

## Modules

### apparmor_profile

A custom Ansible module for managing AppArmor profile fragments.

#### Features

- Contribute AppArmor profile fragments
- Support for multiple roles contributing to the same profile
- Staging directory for fragment merging
- Support for enforce, complain, and disable modes

#### Usage

```yaml
# Using a file from the role
- name: Configure AppArmor profile from file
  exo.apparmor.apparmor_profile:
    name: usr.sbin.nginx
    fragment_src: apparmor/usr.sbin.nginx.rules
    mode: enforce
    state: present

# Using inline content
- name: Configure AppArmor profile inline
  exo.apparmor.apparmor_profile:
    name: usr.sbin.nginx
    fragment: |
      /var/www/html/** r,
      /var/log/nginx/** w,
    mode: enforce
    state: present
```

#### Parameters

- `name`: Name of the AppArmor profile (required)
- `fragment_src`: Path to a file on the control node (searched in files/ and templates/ directories)
- `fragment`: Inline AppArmor profile fragment content
- `mode`: AppArmor mode (enforce, complain, disable) - default: enforce
- `role_name`: Name of the role contributing this fragment
- `state`: present or absent - default: present

Note: Use either `fragment_src` or `fragment`, not both. Files specified in `fragment_src` support Jinja2 templating.

## Installation

Add the collection to your `requirements.yml`:

```yaml
---
collections:
  - name: exo.apparmor
    type: file
    source: ./ansible_collections/exo/apparmor
```

Or for Git installation:

```yaml
---
collections:
  - name: exo.apparmor
    type: git
    source: https://gitlab.com/enexis/exo-ansible-collections/apparmor.git
    version: main
```

## Author

Enexis Team
