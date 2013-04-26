from __future__ import absolute_import
import unittest
import os
import filecmp
import logging
from pprint import pprint

from kamaki.clients.pithos import PithosClient, ClientError
from kamaki.clients import logger

from test.pithosbase import TestPithosBase


logger = logging.getLogger(__name__)


class TestPithosSyncBase(TestPithosBase):

    """A base class for testing pithos sync.

    Provides a set of functions to allow testing the pithos sync library.
    These functions work either locally or remotely.

    The tests work in two folders on the local machine:
    The "local" folder and the "workspace" folder.
    The "local" folder is a working copy given to the pithos sync library
    to work on.
    The pithos sync library is unaware of the "workspace" folder, which is
    used by the testing framework to temporarily construct files and trees
    and download and upload them directly using the kamaki pithos client
    library. It is then used for ensuring correctness and making sure the
    behavior between the test and the library agrees, which is done by
    comparing the two folders.

    Functions that work on the remote machine use the kamaki pithos client
    to perform various operations such as uploading objects and creating
    directories.
    """

    class Local(object):
        def __init__(self, base, local_path):
            self.base = base
            self.path = local_path

        def create_tree(self, file_list):
            self.base.create_tree(self.path, file_list)

        def write_file(self, name, contents):
            self.base.write_file(os.path.join(self.path, name), contents)

        def delete(self):
            self.base.recursive_delete(self.path)

        def make(self):
            self.base.optionally_mkdir(self.path)

        def exists(self):
            return os.path.exists(self.path)

    def setUp(self):
        super(TestPithosSyncBase, self).setUp()

        # the local folder used by the syncing client
        local_path = 'localmirror'
        local_path_2 = 'localmirror2'

        self.local = self.Local(self, local_path)
        self.local2 = self.Local(self, local_path_2)

        # clean up from previous test runs that may have crashed
        self.local.delete()

        # perform initialization on the remote folder (create lockfile etc.)
        self.syncer.init(self.workspace.path, self.remote.path)

        # clean up the workspace after init so that unit tests can cleanly mkdir it
        self.workspace.delete()

        assert(not self.local.exists())
        assert(not self.local.exists())

        try:
            assert(self.remote.container_exists(self.container))
            self.remote.mkdir()
            assert(self.remote.object_exists(self.remote.path))
            assert(self.remote.is_folder(self.remote.path))
            assert(self.remote.folder_empty_but_lock(self.remote.path))
        except ClientError:
            print('\n\nUnable to run test suite.')
            print('Did you export the correct URL using the PITHOS_URL environmental variable?')
            sys.exit(0)

    def assertTreesEqual(self, a, b):
        comparator = filecmp.dircmp(a, b, ['.pithos'])
        self.assertEqual(len(comparator.left_only), 0)
        self.assertEqual(len(comparator.right_only), 0)

    def assertWorkingCopiesMatch(self):
        self.assertTreesEqual(self.local.path, self.local2.path)

    def assertTreesMatch(self):
        self.assertTreesEqual(self.local.path, self.workspace.path)

    def tearDown(self):
        logger.debug('syncbase test suite cleaning up')

        self.local.delete()
        self.local2.delete()

        super(TestPithosSyncBase, self).tearDown()
