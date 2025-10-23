#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Enexis
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: apparmor_profile
short_description: Contribute AppArmor profile fragments
description:
  - This module allows roles to contribute AppArmor profile fragments
  - Fragments are stored in a staging directory and merged later by the baseline
  - Multiple roles can contribute to the same profile
  - Uses an action plugin to read fragment_src files from the control node
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the AppArmor profile (e.g., usr.sbin.nginx)
      - This is the profile name as it will appear in /etc/apparmor.d/
    required: true
    type: str
  fragment_src:
    description:
      - Path to a file containing the AppArmor profile fragment on the control node
      - The file will be searched in the role's files/ and templates/ directories
      - Jinja2 variables in the file will be templated automatically
      - Mutually exclusive with fragment
    type: path
  fragment:
    description:
      - Inline AppArmor profile fragment content
      - Mutually exclusive with fragment_src
    type: str
  mode:
    description:
      - AppArmor mode for the profile.
      - "C(enforce) - Enforce the profile rules"
      - "C(complain) - Log violations but don't enforce"
      - "C(disable) - Disable the profile"
    choices: [ enforce, complain, disable ]
    default: enforce
    type: str
  role_name:
    description:
      - Name of the role contributing this fragment
      - If not provided, will be auto-detected from the role path
    type: str
  state:
    description:
      - Whether the profile fragment should be present or absent
    choices: [ present, absent ]
    default: present
    type: str
  staging_base_dir:
    description:
      - Base directory for storing AppArmor profile fragments
      - Fragments are stored in staging_base_dir/<profile_name>/<role_name>.fragment
    default: /etc/apparmor.d/roles
    type: path
notes:
  - Fragments are stored in staging_base_dir/<profile_name>/<role_name>.fragment (default /etc/apparmor.d/roles)
  - The actual AppArmor profiles are managed by the exo_ansible_role_apparmor role
author:
  - Enexis Team
'''

EXAMPLES = r'''
- name: Contribute nginx AppArmor profile from file (searched in files/ directory)
  apparmor_profile:
    name: usr.sbin.nginx
    fragment_src: apparmor/usr.sbin.nginx.rules
    mode: enforce
    role_name: nginx_role

- name: Add inline nginx AppArmor rules
  apparmor_profile:
    name: usr.sbin.nginx
    fragment: |
      # Custom nginx rules
      /var/www/html/** r,
      /var/log/nginx/** w,
      /run/nginx.pid w,
    mode: enforce
    role_name: nginx_custom
'''

RETURN = r'''
changed:
  description: Whether changes were made
  type: bool
  returned: always
message:
  description: Human readable message about the result
  type: str
  returned: always
fragment_path:
  description: Path where the fragment was stored
  type: str
  returned: when state=present
'''

import os
import tempfile
from ansible.module_utils.basic import AnsibleModule


def ensure_staging_directory(profile_name, staging_base_dir="/etc/apparmor.d/roles"):
    """Ensure the AppArmor staging directory exists for the profile"""
    staging_dir = os.path.join(staging_base_dir, profile_name)
    if not os.path.exists(staging_dir):
        os.makedirs(staging_dir, mode=0o755)
    return staging_dir


def detect_role_name():
    """Try to detect the role name from the call stack"""
    # This is a simple heuristic - in practice, the role_name should be provided
    # or we use a timestamp-based unique identifier
    import time
    return f"role_{int(time.time())}"




def write_fragment(staging_dir, fragment_content, mode, role_name):
    """Write the fragment content to the staging directory"""
    fragment_path = os.path.join(staging_dir, f"{role_name}.fragment")
    
    # Prepend mode as comment
    content_with_mode = f"# Mode: {mode}\n{fragment_content}"
    
    # Write content to temporary file first, then move for atomicity
    temp_fd, temp_path = tempfile.mkstemp(
        dir=staging_dir,
        prefix=f".{role_name}_",
        suffix=".tmp"
    )
    
    try:
        with os.fdopen(temp_fd, 'w') as temp_file:
            temp_file.write(content_with_mode)
        
        # Move temp file to final location
        os.rename(temp_path, fragment_path)
        os.chmod(fragment_path, 0o644)
        
        return fragment_path
    except Exception:
        # Clean up temp file if something went wrong
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def remove_fragment(staging_dir, role_name):
    """Remove the fragment from the staging directory"""
    fragment_path = os.path.join(staging_dir, f"{role_name}.fragment")
    
    if os.path.exists(fragment_path):
        os.unlink(fragment_path)
        
        # Remove directory if empty
        try:
            os.rmdir(staging_dir)
        except OSError:
            # Directory not empty, that's fine
            pass
        
        return True
    return False


def fragment_exists_and_unchanged(staging_dir, fragment_content, mode, role_name):
    """Check if fragment exists and has the same content"""
    fragment_path = os.path.join(staging_dir, f"{role_name}.fragment")
    
    if not os.path.exists(fragment_path):
        return False
    
    try:
        with open(fragment_path, 'r') as f:
            existing_content = f.read()
        
        expected_content = f"# Mode: {mode}\n{fragment_content}"
        return existing_content == expected_content
    except IOError:
        return False


def run_module():
    """Main module function"""
    module_args = dict(
        name=dict(type='str', required=True),
        fragment_src=dict(type='path', required=False),
        fragment=dict(type='str', required=False),
        mode=dict(type='str', default='enforce', choices=['enforce', 'complain', 'disable']),
        role_name=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        staging_base_dir=dict(type='path', default='/etc/apparmor.d/roles')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[['fragment_src', 'fragment']],
        required_one_of=[['fragment_src', 'fragment']]
    )

    profile_name = module.params['name']
    fragment = module.params['fragment']
    mode = module.params['mode']
    role_name = module.params['role_name']
    state = module.params['state']
    staging_base_dir = module.params['staging_base_dir']

    # Auto-detect role name if not provided
    if not role_name:
        role_name = detect_role_name()

    result = dict(
        changed=False,
        message='',
        fragment_path=''
    )

    try:
        # In check mode, we don't create directories
        if not module.check_mode:
            staging_dir = ensure_staging_directory(profile_name, staging_base_dir)
        else:
            staging_dir = os.path.join(staging_base_dir, profile_name)
        
        if state == 'present':
            # In check mode, we can't check if fragment exists if directory doesn't exist
            if not module.check_mode and fragment_exists_and_unchanged(staging_dir, fragment, mode, role_name):
                result['message'] = f"Fragment for profile {profile_name} from role {role_name} already exists and is unchanged"
                result['fragment_path'] = os.path.join(staging_dir, f"{role_name}.fragment")
            else:
                if not module.check_mode:
                    fragment_path = write_fragment(staging_dir, fragment, mode, role_name)
                    result['fragment_path'] = fragment_path
                else:
                    # In check mode, just set what the path would be
                    result['fragment_path'] = os.path.join(staging_dir, f"{role_name}.fragment")
                result['changed'] = True
                result['message'] = f"Fragment for profile {profile_name} from role {role_name} has been {'created' if not module.check_mode else 'would be created'}"
        
        elif state == 'absent':
            if not module.check_mode:
                removed = remove_fragment(staging_dir, role_name)
                if removed:
                    result['changed'] = True
                    result['message'] = f"Fragment for profile {profile_name} from role {role_name} has been removed"
                else:
                    result['message'] = f"Fragment for profile {profile_name} from role {role_name} was not found"
            else:
                fragment_path = os.path.join(staging_dir, f"{role_name}.fragment")
                if os.path.exists(fragment_path):
                    result['changed'] = True
                    result['message'] = f"Fragment for profile {profile_name} from role {role_name} would be removed"
                else:
                    result['message'] = f"Fragment for profile {profile_name} from role {role_name} would not be removed (not found)"

    except Exception as e:
        module.fail_json(msg=f"Failed to manage AppArmor profile fragment: {str(e)}", **result)

    module.exit_json(**result)


if __name__ == '__main__':
    run_module()
