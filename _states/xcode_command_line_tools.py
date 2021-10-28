"""State for managing the Xcode command line tools"""


import logging

import salt.utils.platform


log = logging.getLogger(__name__)


__virtualname__ = 'xcode_command_line_tools'


def __virtual__():
    """Only make available for the Mac platform."""
    if salt.utils.platform.is_darwin():
        return __virtualname__
    else:
        return False, 'state.xcode_command_line_tools only available on macOS'


def installed(name):
    """Ensure that Xcode command line tools are installed."""
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    result = __salt__['xcode_command_line_tools.check']()

    if result:
        ret['result'] = True
        ret['comment'] = 'Xcode command line tools already installed.'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Xcode command line tools would be installed.'
        return ret

    __salt__['xcode_command_line_tools.install']()
    ret['result'] = __salt__['xcode_command_line_tools.check']()

    if not ret['result']:
        ret['comment'] = 'Xcode command line tools were not installed.'
    else:
        ret['comment'] = 'Xcode command line tools were installed.'

    return ret