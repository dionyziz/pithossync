from __future__ import absolute_import
import os

import pithossync
from test.pithosbase import TestPithosBase


class TestInit(TestPithosBase):
    def setUp(self):
        super(TestInit, self).setUp()

    def test_init(self):
        working_copy = self.syncer.init(self.workspace.path, self.remote.path)

        self.assertTrue(os.path.exists(self.workspace.path))
