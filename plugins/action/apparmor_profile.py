#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Schuberg Philis
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text, to_native
import os


class ActionModule(ActionBase):
    """Action plugin for apparmor_profile module
    
    This plugin handles the fragment_src parameter by:
    1. Locating the file in the role's files/ or templates/ directories
    2. Templating it if it's in templates/ or contains Jinja2 variables
    3. Passing the templated content as 'fragment' to the module
    """

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        """Execute the action plugin"""
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp is deprecated

        # Get module arguments
        fragment_src = self._task.args.get('fragment_src', None)
        fragment = self._task.args.get('fragment', None)

        # If fragment_src is provided, we need to read and template it
        if fragment_src:
            if fragment:
                result['failed'] = True
                result['msg'] = "fragment_src and fragment are mutually exclusive"
                return result

            try:
                # Search for the file in role's files/ and templates/ directories
                # This will search in the same way as copy/template modules
                source_file = self._find_needle('files', fragment_src)
                is_template_dir = False
            except AnsibleFileNotFound:
                try:
                    source_file = self._find_needle('templates', fragment_src)
                    is_template_dir = True
                except AnsibleFileNotFound:
                    result['failed'] = True
                    result['msg'] = f"Could not find or access '{fragment_src}' in files/ or templates/ directories"
                    return result

            # Read the file
            try:
                with open(source_file, 'r') as f:
                    file_content = to_text(f.read())
            except Exception as e:
                result['failed'] = True
                result['msg'] = f"Failed to read file '{source_file}': {to_native(e)}"
                return result

            # Template the content (always template, as files can also have Jinja2 vars)
            # Use the templar from the action base
            try:
                templated_content = self._templar.template(
                    file_content,
                    preserve_trailing_newlines=True,
                    escape_backslashes=False,
                    convert_data=False
                )
            except Exception as e:
                result['failed'] = True
                result['msg'] = f"Failed to template file '{source_file}': {to_native(e)}"
                return result

            # Replace fragment_src with fragment in task args
            # This way the module receives the templated content
            self._task.args['fragment'] = templated_content
            del self._task.args['fragment_src']

        # Now execute the module with the modified arguments
        result.update(self._execute_module(
            module_name='exo.apparmor.apparmor_profile',
            module_args=self._task.args,
            task_vars=task_vars
        ))

        return result

