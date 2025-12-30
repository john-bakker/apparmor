# Ansible Collection - apparmor

This collection contains utilities, modules, and roles for managing AppArmor configurations.

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
  apparmor_profile:
    name: usr.sbin.nginx
    fragment_src: apparmor/usr.sbin.nginx.rules
    mode: enforce
    state: present

# Using inline content
- name: Configure AppArmor profile inline
  apparmor_profile:
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

## Roles

### apparmor_profiles

A role for managing AppArmor profile fragments by collecting, merging, and loading profiles from multiple roles.

#### Features

- Installs AppArmor packages
- Collects and merges AppArmor profile fragments from all roles
- Loads merged profiles into AppArmor
- Reloads AppArmor service after changes
- Ensures AppArmor service is running

#### Usage

```yaml
- name: Merge and load AppArmor profiles
  hosts: all
  collections:
    - apparmor
  roles:
    - apparmor_profiles
```

Or using the fully qualified collection name:

```yaml
- name: Merge and load AppArmor profiles
  ansible.builtin.import_role:
    name: apparmor.apparmor_profiles
```

#### Role Variables

See the [role README](roles/apparmor_profiles/README.md) for detailed variable documentation.

## Installation

Add the collection to your `requirements.yml`:

```yaml
---
collections:
  - name: apparmor
    type: file
    source: ./ansible_collections/apparmor
```

Or for Git installation:

```yaml
---
collections:
  - name: apparmor
    type: git
    source: https://github.com/john-bakker/apparmor.git
    version: main
```

## Author

John Bakker
