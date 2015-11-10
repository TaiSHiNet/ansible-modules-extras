#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cloudformation_facts
short_description: View facts about an AWS CloudFormation stack
description:
     - Queries AWS for facts about a given AWS CloudFormation stack
version_added: "1.9"
options:
  stack_name:
    description:
      - name of the cloudformation stack
    required: true
  region:
    description:
      - The AWS region to use. If not specified then the value of the AWS_REGION or EC2_REGION environment variable, if any, is used.
    required: true
    aliases: ['aws_region', 'ec2_region']
    version_added: "1.5"
author: "Andrew McConnell (@amcconnell)"
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Basic task example
- name: Get information about my CloudFormation stack
  cloudformation_facts:
    stack_name: "ansible-cloudformation" 
    region: "us-east-1" 

'''

from datetime import datetime
import json

try:
    import boto.cloudformation
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = err.message
    else:
        error = '%s: %s' % (Exception, err)

    return error

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
         stack_name = dict(required=True),
         region = dict(required=True)
    ))
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True
    )
    
    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')
    
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
    
    result = {}
    
    try:
      conn = boto.cloudformation.connect_to_region(region,**aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))
        
    try:
        stacks = conn.describe_stacks (module.params['stack_name'])
    except boto.exception.BotoServerError, err:
        error_msg = boto_exception(err)
        module.fail_json(msg=error_msg)
        
    if len(stacks) == 1:

        stack = stacks[0]

        result['id'] = stack.stack_id
        result['name'] = stack.stack_name
        result['status'] = stack.stack_status
        result['creation_time'] = stack.creation_time.isoformat()
        result['description'] = stack.description
        result['disable_rollback'] = stack.disable_rollback
        result['timeout_in_minutes'] = stack.timeout_in_minutes
        
        stack_outputs = {}
        for output in stack.outputs:
            stack_outputs[output.key] = output.value
        result['outputs'] = stack_outputs
        
        stack_tags = {}
        for tag in stack.tags:
            stack_tags[tag] = stack.tags[tag]
        result['tags'] = stack_tags;

        stack_params = {}
        for param in stack.parameters:
            stack_params[param.key] = param.value
        result['parameters'] = stack_params;

        stack_capabilities = []
        for capability in stack.capabilities:
            stack_capabilities.append(capability.value)
        result['capabilities'] = stack_capabilities;

        stack_notification_arns = []
        for notification_arn in stack.notification_arns:
            stack_notification_arns.append(notification_arn.value)
        result['notification_arns'] = stack_notification_arns;

        module.exit_json(stack=result)

    else:
        module.fail_json(msg = "Stack not found")

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *
if __name__ == '__main__':
    main()
