from __future__ import absolute_import

import unittest
import os

import pithossync


class TestPithosBase(unittest.TestCase):
    def setUp(self):
        # set up useful settings variables

        self.url = os.getenv('PITHOS_URL', 'https://pithos.okeanos.grnet.gr/v1')
        self.token = os.getenv('ASTAKOS_TOKEN', '')
        
        if self.token == '':
            print('\n\nUnable to run test suite.')
            print('Did you export the ASTAKOS_TOKEN environmental variable?')
            print('You can do this by running:')
            print('ASTAKOS_TOKEN="your_token_here" python runtests.py\n')
            sys.exit(0)

        self.account = 'd8e6f8bb-619b-4ce6-8903-89fabdca024d'
        self.container = 'pithos'
        self.syncer = pithossync.Syncer(self.url, self.token,
                                        self.account, self.container)

    def tearDown(self):
        pass
