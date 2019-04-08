# -*- coding: utf-8 -*-

# Import Salt Testing libs
from salttesting import TestCase, skipIf
from salttesting.helpers import ensure_in_syspath
#from salttesting.mock import patch, call, NO_MOCK, NO_MOCK_REASON  #, MagicMock

ensure_in_syspath('../../../_modules')

import profiles

profiles.__salt__ = {}

class ProfilesTestCase(TestCase):

    def test_payloadcontent_to_uuid(self):
        uuid = profiles._content_to_uuid('ABCDEF')
        print(uuid)


if __name__ == '__main__':
    from ..integration import run_tests
    run_tests(ProfilesTestCase, needs_daemon=False)
