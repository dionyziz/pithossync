from __future__ import absolute_import
import os

from test.syncbase import TestPithosSyncBase
import pithossync


class TestClone(TestPithosSyncBase):
# TODO: assert that remote folder does not exists causes an error during clone
# TODO: assert that local permission denied during clone fails correctly
#    def test_empty_clone(self):
#        """Check if cloning an empty folder works."""
#
#        self.local.make()
#        self.local.write_file('dummy', '')
#        self.assertRaises(pithossync.DirectoryNotEmptyError,
#                          self.syncer.clone,
#                          self.local.path,
#                          self.remote.path)
#        os.unlink(os.path.join(self.local.path, 'dummy'))
#        self.syncer.clone(self.local.path, self.remote.path)
#        # make sure the directory is still empty after cloning an empty
#        # server-side directory
#        os.mkdir(self.workspace.path)
#        self.assertTreesEqual(self.local.path, self.workspace.path)
#        # make sure the server-side directory is not affected
#        # by the clone operation
#        self.assertTrue(self.remote.folder_empty_but_lock(self.remote.path))
#
## TODO: un-init the target dir, then test to assert cloning fails
#
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
#    def test_clone_one_big(self):
#        """Check if cloning a folder with a 100MB binary file works."""
#
#        self.workspace.create_binary('test.bin', 100 * 1024 * 1024)
#        self.workspace.upload('test.bin')
#
#        os.mkdir(self.local.path)
#        self.syncer.clone(self.local.path, self.remote.path)
#        self.assertTreesEqual(self.local.path, self.workspace.path)
#
    def test_clone_tree(self):
        """Create a tree of files and directories and check if it clones."""
        tree = ['red.file', 'green.file', 'blue.file',
                'foo/',
                'foo/red.file', 'foo/green.file', 'foo/blue.file',
                'bar/',
                'bar/quux/',
                'bar/quux/koko.txt',
                'bar/quux/lala.txt',
                'bar/quux/liruliru.txt']

        # create the tree in local_workspace
        self.workspace.create_tree(tree)

        # upload the tree to the server manually by directly
        # utilizing the pithos client
        for file in tree:
            if file[-1] == '/':
                self.remote.mkdir(file[:-1])
            else:
                self.workspace.upload(os.path.join(*file.split('/')))

        # make sure cloning using the pithossync library works correctly
        os.mkdir(self.local.path)
        self.syncer.clone(self.local.path, self.remote.path)

        self.assertTreesEqual(self.local.path, self.workspace.path)
