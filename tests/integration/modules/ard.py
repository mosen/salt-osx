# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import

# Import Salt Testing libs
from salttesting.helpers import ensure_in_syspath
ensure_in_syspath('../../')

# Import salt libs
import integration

class ArdTest(integration.ModuleCase):
    pass


if __name__ == '__main__':
    from integration import run_tests
    run_tests(ArdTest)
