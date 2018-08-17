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


if salt.utils.platform.is_darwin():
    EXMANCMD = '/Applications/Adobe Extension Manager CC/Adobe Extension Manager CC.app/Contents/MacOS/ExManCmd'
    PLATFORM_SWITCH = '--'
elif salt.utils.is_windows():
    EXMANCMD = 'C:\Program Files\Adobe\Adobe Extension Manager CC\ExManCmd.exe'
    PLATFORM_SWITCH = '/'
else:
    EXMANCMD = None


def __virtual__():
    '''
    This module may only run on OSX or Windows, and only if extension manager is installed
    '''
    if EXMANCMD is not None and os.path.exists(EXMANCMD):
        return __virtualname__
    else:
        return False


def items():
    '''
    Get a list of currently installed extensions.

    Returns a dict containing a list for each product name, which is a short name (not always related to the
    executable name)
    '''

    listall_cmd = '"{}" {}disableSendResult true {}list all'.format(EXMANCMD, PLATFORM_SWITCH, PLATFORM_SWITCH)
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


def install(zxp_path, all_users=True):
    '''
    Install a ZXP extension using Extension Manager

    zxp_path
        Full path to the ZXP file to install

    all_users : True
        Whether to install the extension for all users of the computer, default is true.
    '''
    install_cmd = '"{}" {}disableSendResult true {}install "{}"'.format(EXMANCMD, PLATFORM_SWITCH, PLATFORM_SWITCH, zxp_path)
    status = __salt__['cmd.retcode'](install_cmd)

    if status == 0:
        return True
    else:
        log.error('Failed to install CC extension: {}, error code: {}'.format(zxp_path, status))
        return False


def remove(name, all_users=True):
    '''
    Remove an extension using Extension Manager.
    The name may be the short name or the reverse domain form depending on what the developer uses.
    Check the GUI or the output of ccextension.items to see the name

    name
        The name of the extension, shown in extension manager.

    all_users : True
        Whether to remove the extension for all users of the computer, default is true.
    '''
    remove_cmd = '"{}" {}disableSendResult true {}remove "{}"'.format(EXMANCMD, PLATFORM_SWITCH, PLATFORM_SWITCH, name)
    status = __salt__['cmd.retcode'](remove_cmd)

    if status == 0:
        return True
    else:
        log.error('Failed to remove CC extension: {}, error code: {}'.format(name, status))
        return False
