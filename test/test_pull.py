import os

from test.syncbase import TestPithosSyncBase


class TestPush(TestPithosSyncBase):
    def test_pull_one_created(self):
        os.mkdir(self.workspace.path)
        os.mkdir(self.local.path)
        working_copy = self.syncer.clone(self.local.path, self.remote.path)

        self.workspace.write_file('one.txt', 'Goodbye, world!\n')
        self.workspace.upload('one.txt')

        working_copy.pull()

        self.assertTreesMatch()

    def test_pull_one_modified(self):
        os.mkdir(self.workspace.path)

        self.workspace.write_file('one.txt', 'Hello, world!\n')
        self.workspace.upload('one.txt')

        os.mkdir(self.local.path)
        working_copy = self.syncer.clone(self.local.path, self.remote.path)

        self.workspace.write_file('one.txt', 'Goodbye, world!\n')
        self.workspace.upload('one.txt')

        working_copy.pull()

        self.assertTreesMatch()

#    def test_pull_rm(self):
#        pass
#
#        # os.mkdir(self.workspace.path)
#
#        # self.workspace.write_file('one.txt', 'Hello, world!\n')
#
#    def test_pull_rmdir(self):
#        pass
#
#    def test_pull_create_dir(self):
#        pass

# TODO: write tests that check that conflicts occur as expected
