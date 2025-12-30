# apparmor_profiles

Ansible role for managing AppArmor configurations by merging profile fragments from different roles.

This role is part of the apparmor collection.

## Features

- Installs AppArmor packages
- Collects and merges AppArmor profile fragments from all roles
- Loads merged profiles into AppArmor
- Reloads AppArmor service after changes
- Ensures AppArmor service is running

## Requirements

- Linux target hosts (Ubuntu, Debian, SLES)
- apparmor collection (this role is part of the collection)

## Role Variables

```yaml
# AppArmor packages
apparmor_packages:
  - apparmor
  - apparmor-utils

# Service name (may vary per distribution)
apparmor_service_name: apparmor

# Backup existing profiles before merge
apparmor_backup_profiles: true

# Default mode for profiles without explicit mode header
# Valid values: 'enforce', 'complain', 'audit', 'disabled'
apparmor_default_mode: enforce

# Enable enforcement mode
apparmor_enforce_mode: true

# Profile directory
apparmor_profile_dir: /etc/apparmor.d

# Staging directory for role fragments
apparmor_staging_dir: /etc/apparmor.d/roles

# Clean up staging directory after merge (not recommended for production)
apparmor_cleanup_staging: false
```

## Workflow

### 1. Roles contribute fragments

Use the `apparmor_profile` module to add fragments:

```yaml
# Fragment from file (supports Jinja2 templating)
- name: Configure AppArmor profile from file
  apparmor_profile:
    name: usr.sbin.nginx
    fragment_src: apparmor/usr.sbin.nginx.rules
    mode: enforce
    state: present

# Inline fragment
- name: Configure AppArmor profile inline
  apparmor_profile:
    name: usr.sbin.nginx
    fragment: |
      /var/www/html/** r,
      /var/log/nginx/** w,
    mode: enforce
    state: present
```

**Module parameters:**

- `name` (required): Profile name
- `fragment_src`: Path to file on control node (files/ or templates/)
- `fragment`: Inline fragment content
- `mode`: enforce, complain, disable (default: enforce)
- `role_name`: Name of contributing role (optional, auto-detected)
- `state`: present or absent (default: present)

**Note:** Use `fragment_src` OR `fragment`, not both.

### 2. File structure

Fragments are organized per profile:

```text
/etc/apparmor.d/roles/
├── usr.sbin.nginx/
│   ├── nginx_role.fragment
│   └── site_customization.fragment
├── usr.sbin.squid/
│   ├── squid_base.fragment
│   └── squid_ssl_icap.fragment
└── usr.bin.myapp/
    └── myapp_role.fragment
```

### 3. Run merge role

Execute this role in your baseline playbook:

```yaml
- name: Merge AppArmor configurations
  hosts: all
  collections:
    - apparmor
  roles:
    - apparmor_profiles
```

Or using the fully qualified collection name:

```yaml
- name: Merge AppArmor configurations
  ansible.builtin.import_role:
    name: apparmor.apparmor_profiles
```

The role:

- Collects all `.fragment` files per profile directory
- Merges fragments with deduplication
- Creates backup with `.YYMMDDHHMM` timestamp on changes
- Writes merged profile to `/etc/apparmor.d/`
- Loads profiles with correct mode via `apparmor_parser`
- Reloads AppArmor service

## Fragment Format

Fragments can be with or without AppArmor profile wrapper:

**With wrapper (automatically extracted):**

```text
#include <tunables/global>

/usr/bin/myapp {
  #include <abstractions/base>
  /usr/bin/myapp mr,
  /etc/myapp/** r,
}
```

**Without wrapper (rules only):**

```text
/var/www/html/** r,
/var/log/nginx/** w,
capability dac_override,
```

The role automatically detects the format and generates the correct profile structure.

## Important Notes

- **Infrastructure as Code**: Profiles are completely generated from fragments
- **Overwrite**: Manual changes in `/etc/apparmor.d/` will be overwritten
- **Backups**: Automatic backups for every change (`.YYMMDDHHMM` format)
- **Idempotent**: Only updates on actual content changes

## Testing

Molecule tests with full AppArmor kernel support in Docker containers.

### Test Commands

```bash
molecule test      # Full test suite
molecule converge  # Converge only
molecule verify    # Verify only
```

### Test Environment

Docker environment with AppArmor kernel support:

- **Linux**: Native Docker (usually has AppArmor support)
- **macOS**: Colima (not Docker Desktop)

### Docker Configuration

Molecule tests use:

- `privileged: true` - For AppArmor operations
- `/sys/kernel/security` mount (rw) - AppArmor interface
- `/sys/fs/cgroup` mount - For systemd
- `SYS_ADMIN` capability - For profile loading
- `cgroupns_mode: host` - Correct cgroup handling

### Test Coverage

- Profile merging with multiple fragments
- Fragment sources: `fragment_src` and `fragment` (inline)
- Wrapper handling (with/without profile wrapper)
- AppArmor modes: enforce, complain, disable
- Jinja2 templating in fragments
- Rule deduplication
- Backup functionality
- Idempotence checks

## Author

John Bakker
