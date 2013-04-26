from test.syncbase import TestPithosSyncBase


class TestPush(TestPithosSyncBase):
    pass

# TODO: test_push_create
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
