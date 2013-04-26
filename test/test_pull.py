from test.syncbase import TestPithosSyncBase


class TestPush(TestPithosSyncBase):
    pass

# TODO: test_pull_rm
# TODO: test_pull_create
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
