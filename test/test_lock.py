from __future__ import absolute_import

import unittest
import os

import pithossync

from test.pithosbase import TestPithosBase


class TestLock(TestPithosBase):
    def setUp(self):
        super(TestLock, self).setUp()
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
