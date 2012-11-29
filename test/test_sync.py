from __future__ import absolute_import
from kamaki.clients.pithos import PithosClient as pithos, ClientError
import filecmp
import pithossync
import unittest
import os
import pprint
import json

class TestSync(unittest.TestCase):
    def container_exists(self, name):
        available_containers = self.client.list_containers()
        for container in available_containers:
            if container['name'] == name:
                return True
        return False

    def object_exists(self, name):
        try:
            self.client.get_object_info(name)
        except ClientError:
            return False
        return True

    def is_folder(self, name):
        type = self.client.get_object_info(name)['content-type'] 
        return type == 'application/directory' or type == 'application/folder'

    def folder_empty(self, name):
        obj_list = self.client.list_objects()
        for obj in obj_list:
            if obj['name'][0:len(name + '/')] == name + '/':
                return False
        return True

    def remote_recursive_delete(self, name):
        obj_list = self.client.list_objects()
        # delete all the folders' contents
        for obj in obj_list:
            if obj['name'][0:len(name + '/')] == name + '/':
                self.client.object_delete(obj['name'])
        # delete the folder itself
        self.client.object_delete(name)

    def pprint(self, name, data):
        print json.dumps({name: data}, indent=4)

    def assertTreesEqual(self, a, b ):
        comparator = filecmp.dircmp(a, b)
        self.assertEqual(len(comparator.left_only), 0)
        self.assertEqual(len(comparator.right_only), 0)

    def setUp(self):
        # set up useful settings variables
        self.url = 'https://pithos.okeanos.grnet.gr/v1'
        self.token = os.getenv('ASTAKOS_TOKEN')
        self.account = 'dionyziz@gmail.com'
        self.container = 'pithos'
        self.syncer = pithossync.Syncer(self.url, self.token, self.account, self.container)
        # the local folder used by the syncing client
        self.local = 'localmirror'
        # the local folder used by the tests 
        self.local_workspace = 'localworkspace'
        # the name of the remote folder within the pithos container
        self.folder = 'sync-test'
        self.client = pithos(self.url, self.token, self.account, self.container)

        # clean up from previous test runs that may have crashed
        self.local_recursive_delete(self.local)
        self.local_recursive_delete(self.local_workspace)

        assert(not os.path.exists(self.local))
        assert(not os.path.exists(self.local_workspace))

        try:
            assert(self.container_exists(self.container))
            self.client.create_directory(self.folder)
            assert(self.object_exists(self.folder))
            assert(self.is_folder(self.folder))
            assert(self.folder_empty(self.folder))
        except ClientError as e:
            print('\n\nUnable to run test suite.')
            print('Did you export the ASTAKOS_TOKEN environmental variable?')
            print('You can do this by running:')
            print('ASTAKOS_TOKEN="your_token_here" python runtests.py\n')

#    def test_empty_clone(self):
#        """Check if cloning an empty folder works."""
#
#        os.mkdir(self.local)
#        self.local_write_file('dummy', '')
#        self.assertRaises(
#            pithossync.DirectoryNotEmptyError,
#            self.syncer.clone,
#            self.local,
#            self.folder
#        )
#        os.unlink(os.path.join(self.local, 'dummy'))
#        self.syncer.clone(self.local, self.folder)
#        # make sure the directory is still empty after cloning an empty
#        # server-side directory
#        os.mkdir(self.local_workspace)
#        self.assertTreesEqual(self.local, self.local_workspace)
#        # make sure the server-side directory is not affected by the clone operation
#        self.assertTrue(self.folder_empty(self.folder))
# 
#    def test_clone_one_text(self):
#        """Check if cloning a folder containing a single text file works.
#        
#        Create one text test file on the server and make sure it's
#        downloaded by the client during sync.
#        """
#
#        os.mkdir(self.local_workspace)
#        self.workspace_write_file('one.txt', 'Hello, world!\n')
#        self.workspace_upload('one.txt')
#
#        os.mkdir(self.local)
#        self.syncer.clone(self.local, self.folder)
#
#        self.assertTreesEqual(self.local, self.local_workspace)

    def workspace_create_random(self, name, size):
        try:
            os.mkdir(self.local_workspace)
        except OSError:
            # directory already exists
            pass

        f = open(os.path.join(self.local_workspace, name), 'w')
        for i in xrange(size / 8):
            f.write(8 * '\0')
        f.flush()
        f.close()

    def workspace_download(self, name):
        f = open(os.path.join(self.local_workspace, name), 'wb+')
        self.client.download_object(self.folder + '/' + name, f)
        f.close()

    def workspace_upload(self, name):
        f = open(os.path.join(self.local_workspace, name), 'r')
        self.client.upload_object(self.folder + '/' + name, f)
        f.close()

#    def test_clone_one_bin(self):
#        """Check if cloning a folder with a single binary file works."""
#        self.workspace_create_random('test.bin', 8)
#        self.workspace_upload('test.bin')
#
#        os.mkdir(self.local)
#        self.syncer.clone(self.local, self.folder)
#        self.assertTreesEqual(self.local, self.local_workspace)

#    def test_clone_one_big(self):
#        """Check if cloning a folder with a 100MB binary file works."""
#
#        self.workspace_create_random('test.bin', 100 * 1024 * 1024)
#        self.workspace_upload('test.bin')
#
#        os.mkdir(self.local)
#        self.syncer.clone(self.local, self.folder)
#        self.assertTreesEqual(self.local, self.local_workspace)
#
    def write_file(self, name, contents):
        f = open(name, 'w')
        f.write(contents)
        f.close()

    def local_write_file(self, name, contents):
        self.write_file(os.path.join(self.local, name), contents)

    def workspace_write_file(self, name, contents):
        self.write_file(os.path.join(self.local_workspace, name), contents)

    def create_tree(self, file_list):
        try:
            os.mkdir(self.local_workspace)
        except:
            pass
        for file in file_list:
            path = file.split('/')
            components = ''
            for component in path[:-1]:
                components += component
                try:
                    os.mkdir(os.path.join(self.local_workspace, components))
                except OSError:
                    # directory already exists
                    pass
                components += '/'
            f = open(os.path.join(self.local_workspace, file), 'w')
            f.write(file)
            f.close()

#    def test_clone_tree(self):
#        """Create a tree of files and directories and check if it clones."""
#        tree = ['red.file', 'green.file', 'blue.file',
#                'foo/red.file', 'foo/green.file', 'foo/blue.file',
#                'bar/quux/koko.txt', 'bar/quux/lala.txt', 'bar/quux/liruliru.txt']
#        self.create_tree(tree)
#        # TODO: also create the directories on the server
#        for file in tree:
#            self.workspace_upload(os.path.join(*file.split('/')))
#        os.mkdir(self.local)
#        self.syncer.clone(self.local, self.folder)
#        self.assertTreesEqual(self.local, self.local_workspace)

    def test_push_one_created(self):
        os.mkdir(self.local)
        os.mkdir(self.local_workspace)

        # sync an empty directory from the server
        working_copy = self.syncer.clone(self.local, self.folder)

        # create a text file in our local mirror
        self.local_write_file('one.txt', 'Hello, world')
        # push our changes (file creation) to the server
        working_copy.push()

        # the file should now be uploaded to the server
        # directly download the file using the pithos client
        # to verify we have succeeded
        self.workspace_download('one.txt')

        # make sure the exact same file was downloaded
        self.assertTreesEqual(self.local, self.local_workspace)

    def test_push_one_modified(self):
        os.mkdir(self.local_workspace)

        os.mkdir(self.local)
        working_copy = self.syncer.clone(self.local, self.folder)

        # create a file in our local mirror
        self.local_write_file('one.txt', 'Hello, world!\n')
        # push it to the server
        working_copy.push()

        # modify the file
        self.local_write_file('one.txt', 'Goodbye, world!\n')
        # push it to the server
        working_copy.push()
        # download it independently
        self.workspace_download('one.txt')

        # make sure the modified file has been synchronized
        self.assertTreesEqual(self.local, self.local_workspace)

#    def test_pull_one_created(self):
#        os.mkdir(self.local_workspace)
#        os.mkdir(self.local)
#        working_copy = self.syncer.clone(self.local, self.folder)
#
#        self.workspace_write_file('one.txt', 'Goodbye, world!\n')
#        self.workspace_upload('one.txt')
#
#        working_copy.pull()
#
#        self.assertTreesEqual(self.local, self.local_workspace)
#
#    def test_pull_one_modified(self):
#        os.mkdir(self.local_workspace)
#
#        self.workspace_write_file('one.txt', 'Hello, world!\n')
#
#        os.mkdir(self.local)
#        working_copy = self.syncer.clone(self.local, self.folder)
#
#        self.workspace_write_file('one.txt', 'Goodbye, world!\n')
#        self.workspace_upload('one.txt')
#
#        working_copy.pull(self.local)
#
#        self.assertTreesEqual(self.local, self.local_workspace)
#    def test_sync(self):
#        pass

# TODO: assert that directory removals alone are pushed

    def local_recursive_delete(self, folder):
        """rm -rf folder"""
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(folder)

    def tearDown(self):
        """Clean up all temporary directories on the server and on the client.
        
        Local: self.local, self.local_workspace
        Remote: self.folder
        """
        self.local_recursive_delete(self.local)
        self.local_recursive_delete(self.local_workspace)
        self.remote_recursive_delete(self.folder)
