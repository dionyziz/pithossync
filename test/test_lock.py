import unittest
import os

import pithossync


class TestLock(unittest.TestCase):
    def setUp(self):
        self.url = os.getenv('PITHOS_URL', 'https://pithos.okeanos.grnet.gr/v1')
        self.token = os.getenv('ASTAKOS_TOKEN', '')

        self.account = 'd8e6f8bb-619b-4ce6-8903-89fabdca024d'
        self.container = 'pithos'
        self.syncer = pithossync.Syncer(self.url, self.token,
                                        self.account, self.container)

        self.working_copy_path = 'unittest_working_copy'
        self.mirrored_folder = 'unittest_mirrored_folder'

#    def test_obtain(self):
#        working_copy = self.syncer.init(self.working_copy_path, self.mirrored_folder)
#
#        lock = pithossync.Lock(working_copy)
#        lock.obtain()
#
#        lock2 = pithossync.Lock(working_copy)
#
#        self.assertRaises(pithossync.LockViolationError, lock2.obtain)
#        
#        lock.release()
#
#        lock2.obtain()
#        lock2.release()

    def tearDown(self):
        pass
