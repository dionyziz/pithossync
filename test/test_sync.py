from kamaki.clients.pithos import PithosClient as pithos, ClientError
import filecmp
import pithossync
import unittest
import os
import pprint
import json

class TestSync(unittest.TestCase):
    def container_exists(self, name):
        availableContainers = self.client.list_containers()
        for container in availableContainers:
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
        objList = self.client.list_objects()
        for obj in objList:
            if obj['name'][0:len(name + '/')] == name + '/':
                return False
        return True
    def recursive_delete(self, name):
        objList = self.client.list_objects()
        # delete all the folders' contents
        for obj in objList:
            if obj['name'][0:len(name + '/')] == name + '/':
                self.client.object_delete(obj['name'])
        # delete the folder itself
        self.client.object_delete(name)
    def pprint(self, name, data):
        print json.dumps({name: data}, indent=4)
    def set_up(self):
        self.url = 'https://pithos.okeanos.grnet.gr/v1'
        self.token = os.getenv('ASTAKOS_TOKEN')
        self.account = 'dionyziz@gmail.com'
        self.container = 'pithos'
        # self.syncer = pithossync.Syncer(url, token, account, self.container)
        self.local = 'localmirror'
        self.localWorkspace = 'localworkspace'
        self.folder = 'sync-test'
        assert(not os.path.exists(self.local))
        assert(not os.path.exists(self.localWorkspace))
        self.client = pithos(self.url, self.token, self.account, self.container)
        try:
            assert(self.container_exists(self.container))
            self.client.create_directory(self.folder)
            assert(self.object_exists(self.folder))
            assert(self.is_folder(self.folder))
            assert(self.folder_empty(self.folder))
        except ClientError:
            print('Unable to run test suite.')
            print('Did you export the ASTAKOS_TOKEN environmental variable?')
            print('You can do this by running:')
            print('ASTAKOS_TOKEN="your_token_here" python runtests.py')
    # def test_hello(self):
    #     print('Hello world!')
    def test_emptyClone(self):
        os.mkdir(self.local)
        open(self.local + '/dummy', 'w').close()
        self.assertRaises(
            pithossync.DirectoryNotEmptyError,
            self.syncer.clone,
            self.local,
            self.folder
        )
        os.unlink(self.local + '/dummy')
        self.syncer.clone(self.local, self.folder)
        # make sure the directory is still empty after cloning an empty
        # server-side directory
        for root, dirs, files in os.walk(self.local, topdown=False):
            self.assertEqual(root, self.local)
            self.assertEqual(len(files), 0)
            self.assertEqual(len(dirs), 0)
        # make sure the server-side directory is not affected by the clone operation
        self.assertTrue(self.folderEmpty(self.folder))
    def assert_treesEqual(self, a, b):
        comparator = filecmp.dircmp(self.local, self.localWorkspace)
        self.assertEqual(len(comparator.left_only), 0)
        self.assertEqual(len(comparator.right_only), 0)
    def test_cloneOneText(self):
        """Check if cloning a folder containing a single text file works.
        
        Create one text test file on the server and make sure it's
        downloaded by the client during sync.
        """

        os.mkdir(self.localWorkspace)
        hello = 'Hello, world!\n'
        f = open(self.localWorkspace + '/one.txt', 'w')
        f.write(hello)
        f.close()

        f = open(self.localWorkspace + '/one.txt', 'r')
        self.client.upload_object(self.folder + '/one.txt', f)
        f.close()

        os.mkdir(self.local)
        self.syncer.clone(self.local, self.folder)

        for root, dirs, files in os.walk(self.local):
            # no subdirectories should have been created
            self.assertEqual(root, self.local)
            self.assertEqual(len(dirs), 0)
            # only one file should be created
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0], 'one.txt')

        self.assertTrue(os.path.exists(self.local + '/one.txt'))
        f = open(self.local + '/one.txt', 'r')
        contents = f.read()
        self.assertEqual(contents, hello)
    # def test_cloneOneBin(self):
    # def test_cloneOneBig(self):
    # def test_push(self):
    #     pass
    # def test_pull(self):
    #     pass
    # def test_sync(self):
    #     pass
    def tear_down(self):
        """ Clean up all temporary directories on the server and on the client
        and then delete them:
        
        Local: self.local, self.localWorkspace
        Remote: self.folder

        """
        if os.path.exists(self.local):
            for root, dirs, files in os.walk(self.local, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
            os.rmdir(self.local)
        if os.path.exists(self.localWorkspace):
            for root, dirs, files in os.walk(self.localWorkspace, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
            os.rmdir(self.localWorkspace)
        self.recursive_delete(self.folder)
