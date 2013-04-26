from __future__ import absolute_import
import unittest
import os
import logging

from kamaki.clients.pithos import PithosClient, ClientError
import pithossync


logger = logging.getLogger(__name__)


class TestPithosBase(unittest.TestCase):
    class Remote(object):
        def __init__(self, base, remote_path):
            self.path = remote_path
            self.base = base
            self.client = base.client

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
            return type in ['application/directory', 'application/folder']

        def folder_empty(self, name):
            obj_list = self.client.list_objects()
            for obj in obj_list:
                if obj['name'][0:len(name + '/')] == name + '/':
                    return False
            return True
        
        def folder_empty_but_lock(self, name):
            obj_list = self.client.list_objects()
            for obj in obj_list:
                if obj['name'][0:len(name + '/')] == name + '/' and obj['name'][len(name + '/'):] != '.pithos_sync':
                    return False
            return True

        def recursive_delete(self, name):
            obj_list = self.client.list_objects()

            # delete all the folders' contents
            for obj in obj_list:
                if obj['name'][0:len(name + '/')] == name + '/':
                    self.client.object_delete(obj['name'])
            # delete the folder itself
            self.client.object_delete(name)

        def mkdir(self, name = ''):
            if name == '':
                dir = self.path
            else:
                dir = self.path + '/' + name
            self.client.create_directory(dir)

    class Workspace(object):
        def __init__(self, base, workspace_path):
            self.base = base
            self.client = base.client
            self.path = workspace_path

        def create_binary(self, name, size):
            """Creates a local binary file of arbitrary size for testing.

            The file is a zero file created in local_workspace and with size
            specified in KB.
            """
            self.make()

            f = open(os.path.join(self.path, name), 'w')
            for i in xrange(size):
                f.write(1024 * '\0')
            f.flush()
            f.close()

        def write_file(self, name, contents):
            self.base.write_file(os.path.join(self.path, name), contents)

        def create_tree(self, file_list):
            self.base.create_tree(self.path, file_list)

        def download(self, name):
            path = os.path.join(self.path, *name.split('/'))
            f = open(path, 'wb+')
            self.client.download_object(self.base.remote.path + '/' + name, f)
            f.close()

        def upload(self, name):
            f = open(os.path.join(self.path, *name.split('/')), 'r')
            self.client.upload_object(self.base.remote.path + '/' + name, f)
            f.close()

        def delete(self):
            self.base.recursive_delete(self.path)

        def make(self):
            self.base.optionally_mkdir(self.path)

        def exists(self):
            return os.path.exists(self.path)


    def write_file(self, name, contents):
        f = open(name, 'w')
        f.write(contents)
        f.close()

    def create_tree(self, root, file_list):
        """Creates a local tree of files for testing.

        file_list is a list of files in the following format:
        It is a list of strings that describe file and folder paths.
        All use forward slashes UNIX-style to separate files and folders.
        Forward-slashes are then replaced to follow the host OS.
        The tree may contain empty folders.
        Each file written is a text file containing a single line with its
        own filename.
        """

        self.optionally_mkdir(root)
        for file in file_list:
            if file[-1] == '/':
                components = file[:-1].split('/')
                path = os.path.join(root, *components)
                os.mkdir(path)
            else:
                components = file.split('/')
                filename = os.path.join(root, *components)
                f = open(filename, 'w')
                f.write(file)
                f.close()

    def recursive_delete(self, folder):
        """rm -rf folder"""
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(folder)

    def optionally_mkdir(self, folder):
        try:
            os.mkdir(folder)
        except:
            pass

    def setUp(self):
        # set up useful settings variables

        self.url = os.getenv('PITHOS_URL', 'https://pithos.okeanos.grnet.gr/v1')
        self.token = os.getenv('ASTAKOS_TOKEN', '')
        
        if self.token == '':
            print('\n\nUnable to run test suite.')
            print('Did you export the ASTAKOS_TOKEN environmental variable?')
            print('You can do this by running:')
            print('ASTAKOS_TOKEN="your_token_here" python runtests.py\n')
            sys.exit(0)

        self.account = 'd8e6f8bb-619b-4ce6-8903-89fabdca024d'
        self.container = 'pithos'
        self.syncer = pithossync.Syncer(self.url, self.token,
                                        self.account, self.container)

        self.client = PithosClient(self.url, self.token,
                                   self.account, self.container)

        # the local folder used by the tests, unavailable to the code being tested
        workspace_path = 'localworkspace'
        # the name of the remote folder within the pithos container
        remote_path = 'sync-test'

        self.workspace = self.Workspace(self, workspace_path)
        self.remote = self.Remote(self, remote_path)

        # clean up from previous test runs that may have crashed
        self.workspace.delete()
        self.remote.recursive_delete(self.remote.path)

    def tearDown(self):
        """Clean up all temporary directories on the server and on the client.

        Local: self.local.path, self.workspace.path
        Remote: self.remote.path
        """

        logger.debug('pithosbase test suite cleaning up')

        self.workspace.delete()
        self.remote.recursive_delete(self.remote.path)
