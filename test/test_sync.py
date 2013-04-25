from __future__ import absolute_import
import os
import sys
import logging

from kamaki.clients.pithos import PithosClient, ClientError
from kamaki.clients import logger

import pithossync
from test.syncbase import TestPithosSyncBase


class TestSync(TestPithosSyncBase):
    def setUp(self):
        super(TestSync, self).setUp()

        # clean up from previous test runs that may have crashed
        self.local.delete()
        self.workspace.delete()
        self.remote.recursive_delete(self.remote.path)

        # perform initialization on the remote folder (create lockfile etc.)
        self.syncer.init(self.workspace.path, self.remote.path)

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

    def test_empty_clone(self):
        """Check if cloning an empty folder works."""

        self.local.make()
        self.local.write_file('dummy', '')
        self.assertRaises(pithossync.DirectoryNotEmptyError,
                          self.syncer.clone,
                          self.local.path,
                          self.remote.path)
        os.unlink(os.path.join(self.local.path, 'dummy'))
        self.syncer.clone(self.local.path, self.remote.path)
        # make sure the directory is still empty after cloning an empty
        # server-side directory
        os.mkdir(self.workspace.path)
        self.assertTreesEqual(self.local.path, self.workspace.path)
        # make sure the server-side directory is not affected
        # by the clone operation
        self.assertTrue(self.remote.folder_empty_but_lock(self.remote.path))

# TODO: un-init the target dir, then test to assert cloning fails

#    def test_clone_one_text(self):
#        """Check if cloning a folder containing a single text file works.
#
#        Create one text test file on the server and make sure it's
#        downloaded by the client during sync.
#        """
#
#        os.mkdir(self.workspace.path)
#        self.workspace.write_file('one.txt', 'Hello, world!\n')
#        self.workspace.upload('one.txt')
#
#        os.mkdir(self.local.path)
#        self.syncer.clone(self.local.path, self.remote.path)
#
#        self.assertTreesEqual(self.local.path, self.workspace.path)
#
#    def test_clone_one_bin(self):
#        """Check if cloning a folder with a single binary file works."""
#        self.workspace.create_binary('test.bin', 8)
#        self.workspace.upload('test.bin')
#
#        os.mkdir(self.local.path)
#        self.syncer.clone(self.local.path, self.remote.path)
#        self.assertTreesEqual(self.local.path, self.workspace.path)
#
##    def test_clone_one_big(self):
##        """Check if cloning a folder with a 100MB binary file works."""
##
##        self.workspace.create_binary('test.bin', 100 * 1024 * 1024)
##        self.workspace.upload('test.bin')
##
##        os.mkdir(self.local.path)
##        self.syncer.clone(self.local.path, self.remote.path)
##        self.assertTreesEqual(self.local.path, self.workspace.path)
##
#    def test_clone_tree(self):
#        """Create a tree of files and directories and check if it clones."""
#        tree = ['red.file', 'green.file', 'blue.file',
#                'foo/',
#                'foo/red.file', 'foo/green.file', 'foo/blue.file',
#                'bar/',
#                'bar/quux/',
#                'bar/quux/koko.txt',
#                'bar/quux/lala.txt',
#                'bar/quux/liruliru.txt']
#
#        # create the tree in local_workspace
#        self.workspace.create_tree(tree)
#
#        # upload the tree to the server manually by directly
#        # utilizing the pithos client
#        for file in tree:
#            if file[-1] == '/':
#                self.remote.mkdir(file[:-1])
#            else:
#                self.workspace.upload(os.path.join(*file.split('/')))
#
#        # make sure cloning using the pithossync library works correctly
#        os.mkdir(self.local.path)
#        self.syncer.clone(self.local.path, self.remote.path)
#
#        self.assertTreesEqual(self.local.path, self.workspace.path)
#
#    def test_push_one_created(self):
#        self.local.make()
#        self.workspace.make()
#
#        # sync an empty directory from the server
#        working_copy = self.syncer.clone(self.local.path, self.remote.path)
#
#        # create a text file in our local mirror
#        self.local.write_file('one.txt', 'Hello, world')
#        # push our changes (file creation) to the server
#        working_copy.push()
#
#        # the file should now be uploaded to the server
#        # directly download the file using the pithos client
#        # to verify we have succeeded
#        self.workspace.download('one.txt')
#
#        # make sure the exact same file was downloaded
#        self.assertTreesMatch()
#
#    def test_push_one_modified(self):
#        self.workspace.make()
#        self.local.make()
#        working_copy = self.syncer.clone(self.local.path, self.remote.path)
#
#        # create a file in our local mirror
#        self.local.write_file('one.txt', 'Hello, world!\n')
#        # push it to the server
#        working_copy.push()
#
#        # modify the file
#        self.local.write_file('one.txt', 'Goodbye, world!\n')
#        # push it to the server
#        working_copy.push()
#        # download it independently
#        self.workspace.download('one.txt')
#
#        # make sure the modified file has been synchronized
#        self.assertTreesMatch()
#
#    def test_push_later(self):
#        os.mkdir(self.workspace.path)
#        os.mkdir(self.local.path)
#
#        self.syncer.clone(self.local.path, self.remote.path)
#
#        syncer2 = pithossync.Syncer(self.url, self.token,
#                                    self.account, self.container)
#        working_copy = syncer2.working_copy(self.local.path)
#
#        self.local.write_file('one.txt', 'Hello, world!\n')
#        working_copy.push()
#
#        self.syncer.clone(self.local2.path, self.remote.path)
#
#        self.assertWorkingCopiesMatch()
#
#    def test_pull_one_created(self):
#        os.mkdir(self.workspace.path)
#        os.mkdir(self.local.path)
#        working_copy = self.syncer.clone(self.local.path, self.remote.path)
#
#        self.workspace.write_file('one.txt', 'Goodbye, world!\n')
#        self.workspace.upload('one.txt')
#
#        working_copy.pull()
#
#        self.assertTreesMatch()
#
#    def test_pull_one_modified(self):
#        os.mkdir(self.workspace.path)
#
#        self.workspace.write_file('one.txt', 'Hello, world!\n')
#
#        os.mkdir(self.local.path)
#        working_copy = self.syncer.clone(self.local.path, self.remote.path)
#
#        self.workspace.write_file('one.txt', 'Goodbye, world!\n')
#        self.workspace.upload('one.txt')
#
#        working_copy.pull()
#
#        self.assertTreesMatch()
#
#    def test_push_rmdir(self):
#        tree = ['foo/',
#                'foo/biz/',
#                'foo/biz/baz/',
#                'bar/',
#                'bar/quux/']
#
#        working_copy = self.syncer.clone(self.local.path, self.remote.path)
#        self.local.create_tree(tree)
#        working_copy.push()
#
#        working_copy2 = self.syncer.clone(self.local2.path, self.remote.path)
#
#        os.rmdir(os.path.join(self.local.path, 'foo', 'biz', 'baz'))
#        os.rmdir(os.path.join(self.local.path, 'foo', 'biz'))
#        os.rmdir(os.path.join(self.local.path, 'foo'))
#
#        working_copy.push()
#        working_copy2.pull()
#
#        self.assertWorkingCopiesMatch()
#
#    def test_push_rm(self):
#        tree = ['foo/',
#                'foo/biz/',
#                'foo/biz/baz',
#                'foo/biz/koko',
#                'foo/biz/liruliru/',
#                'foo/lala/',
#                'bar/',
#                'bar/quux']
#
#        working_copy = self.syncer.clone(self.local.path, self.remote.path)
#        self.local.create_tree(tree)
#        working_copy.push()
#
#        os.rmdir(os.path.join(self.local.path, 'foo', 'lala'))
#        os.remove(os.path.join(self.local.path, 'foo', 'biz', 'baz'))
#
#        working_copy2 = self.syncer.clone(self.local2.path, self.remote.path)
#
#        working_copy.push()
#        working_copy2.pull()
#
#        self.assertWorkingCopiesMatch()

# TODO: assert that remote folder does not exists causes an error during clone
# TODO: assert that local permission denied during clone fails correctly
# TODO: test that using local directories that end both in a '/' and not in one
#       works correctly
# TODO: create a specific Access Denied exception and throw it by parsing kamaki errors correctly
# TODO: test_init
# TODO: test_pull_rm
# TODO: test_push_create
# TODO: test_pull_create
# TODO: test replace file with folder with same name and vice versa
# TODO: test creation/modification/deletion race conditions (how?)

    def tearDown(self):
        """Clean up all temporary directories on the server and on the client.

        Local: self.local.path, self.workspace.path
        Remote: self.remote.path
        """
        logging.debug('test_sync test suite cleaning up')
        self.local.delete()
        self.local2.delete()
        self.workspace.delete()
        self.remote.recursive_delete(self.remote.path)
