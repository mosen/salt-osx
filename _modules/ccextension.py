# -*- coding: utf-8 -*-
'''
Install and remove ZXP extensions via Extension Manager CC
'''

import logging
import os.path
import re
import salt.utils

log = logging.getLogger(__name__)
__virtualname__ = 'ccextension'


if salt.utils.is_darwin():
    EXMANCMD = '/Applications/Adobe Extension Manager CC/Adobe Extension Manager CC.app/Contents/MacOS/ExManCmd'
elif salt.utils.is_windows():
    EXMANCMD = 'C:\Program Files\Adobe\Adobe Extension Manager CC\ExManCmd.exe'
else:
    EXMANCMD = None


def __virtual__():
    '''
    This module may only run on OSX or Windows, and only if extension manager is installed
    '''
    if EXMANCMD is not None and os.path.exists(EXMANCMD):
        return __virtualname__
    else:
        return None


def items():
    '''
    Get a list of currently installed extensions.

    Returns a dict containing a list for each product name, which is a short name (not always related to the
    executable name)
    '''
    platform_switch = '--' if salt.utils.is_darwin() else '/'
    listall_cmd = '"{}" {}list all'.format(EXMANCMD, platform_switch)
    output = __salt__['cmd.run'](listall_cmd)


    items = dict()
    current_product = list()
    current_product_name = None

    # 1 extension installed for Dreamweaver CC
    for line in output.splitlines():
        if re.match('[0-9]+ extensions installed for (.*)', line):
            if current_product_name is not None:
                items[current_product_name] = current_product
                current_product = list()

            current_product_name = re.search('[0-9]* extensions installed for (.*)', line).group(1)
        elif re.match('^\s(Enabled|Disabled)', line):
            extension_attrs = line.split()
            version = extension_attrs.pop()
            enabled = extension_attrs.pop(0)
            name = ' '.join(extension_attrs)
            current_product.append({'enabled': enabled, 'name': name, 'version': version})

    if current_product_name is not None:
        items[current_product_name] = current_product

    return items

