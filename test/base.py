import unittest
import os
import filecmp
from pprint import pprint

from kamaki.clients.pithos import ClientError

class TestPithosSyncBase(unittest.TestCase):

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
                print('Error getting object info for object "%s"' % name)
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

        def recursive_delete(self, name):
            print("Listing objects")
            obj_list = self.client.list_objects()
            print("Done listing")

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
            """Creates a local tree of files for testing.

            file_list is a list of files in the following format:
            It is a list of strings that describe file and folder paths.
            All use forward slashes UNIX-style to separate files and folders.
            Forward-slashes are then replaced to follow the host OS.
            The tree may contain empty folders.
            Each file written is a text file containing a single line with its
            own filename.
            """

            self.make()
            for file in file_list:
                if file[-1] == '/':
                    components = file[:-1].split('/')
                    path = os.path.join(self.path, *components)
                    os.mkdir(path)
                else:
                    components = file.split('/')
                    filename = os.path.join(self.path, *components)
                    f = open(filename, 'w')
                    f.write(file)
                    f.close()

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

    class Local(object):
        def __init__(self, base, local_path):
            self.base = base
            self.path = local_path

        def write_file(self, name, contents):
            self.base.write_file(os.path.join(self.path, name), contents)

        def delete(self):
            self.base.recursive_delete(self.path)

        def make(self):
            self.base.optionally_mkdir(self.path)

        def exists(self):
            return os.path.exists(self.path)

    def setUp(self, workspace_path, local_path, remote_path):
        self.workspace = self.Workspace(self, workspace_path)
        self.local = self.Local(self, local_path)
        self.remote = self.Remote(self, remote_path)

    def assertTreesEqual(self, a, b):
        comparator = filecmp.dircmp(a, b)
        self.assertEqual(len(comparator.left_only), 0)
        self.assertEqual(len(comparator.right_only), 0)

    def assertTreesMatch(self):
        self.assertTreesEqual(self.local.path, self.workspace.path)

    def write_file(self, name, contents):
        f = open(name, 'w')
        f.write(contents)
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
