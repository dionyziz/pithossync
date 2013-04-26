from __future__ import absolute_import
import os
import sys
import logging

from kamaki.clients.pithos import PithosClient, ClientError

import pithossync
from test.syncbase import TestPithosSyncBase


class TestSync(TestPithosSyncBase):
# TODO: test that using local directories that end both in a '/' and not in one
#       works correctly
# TODO: create a specific Access Denied exception and throw it by parsing kamaki errors correctly
# TODO: test replace file with folder with same name and vice versa
# TODO: test creation/modification/deletion race conditions (how?)
    pass
