from kamaki.clients.pithos import PithosClient, ClientError
import os
import ConfigParser


class DirectoryNotEmptyError(Exception):
    pass


class FileNotFoundError(Exception):
    pass

class InvalidWorkingCopy(Exception):
    pass


class WorkingCopy:
    """Represents a local copy of a directory cloned from the Pithos+ server."""

    def download(self, name):
        remotepath = self.folder + '/' + name
        path = os.path.join(self.local, os.path.join(*name.split('/')))
        try:
            f = open(path, 'wb+')
        except:
            print("Failed to write to local file '%s'." % path)
            return
        try:
            self.syncer.client.download_object(remotepath, f)
        except ClientError:
            print("Failed to download %s." % remotepath)
            return
        f.close()
        print("Downloaded remote file '%s' into %s (%i bytes)" %
              (remotepath, path, os.stat(path).st_size))

    def upload(self, destination, source):
        f = open(source, 'r')
        self.syncer.client.upload_object(self.folder + '/' + destination, f)
        f.close()
        print("Uploaded local file '%s' (%i bytes)" %
              (source, os.stat(source).st_size))

    def remote_mkdir(self, name):
        dir = self.folder + '/' + name
        self.syncer.client.create_directory(dir)
        print("Created remote directory '%s'." % dir)

    def is_folder(self, type):
        return type in ['application/directory', 'application/folder']

    def recursive_download(self, name):
        obj_list = self.syncer.client.list_objects()
        count_objects = 0
        for obj in obj_list:
            file = obj['name']
            type = obj['content_type']
            if file[0:len(name + '/')] == name + '/':
                path_after_folder = file[len(name + '/'):]
                count_objects += 1
                if self.is_folder(type):
                    try:
                        components = path_after_folder.split('/')
                        path_to_create = os.path.join(*components)
                        os.makedirs(os.path.join(self.local, path_to_create))
                        print("Created directory %s"
                              % os.path.join(self.local, path_after_folder))
                    except OSError:
                        pass
                else:
                    components = path_after_folder.split('/')
                    try:
                        os.makedirs(os.path.join(self.local, *components[:-1]))
                        print("Created directory %s"
                              % os.path.join(self.local, *components[:-1]))
                    except OSError:
                        pass
                    self.download(file[len(name + '/'):])
        print("Cloning successful.")
        print("Created %i local objects out of %i total objects in container."
              % (count_objects, len(obj_list)))

    def remote_recursive_delete_contents(self, name):
        obj_list = self.syncer.client.list_objects()
        # delete all the folders' contents
        for obj in obj_list:
            if obj['name'][0:len(name + '/')] == name + '/':
                self.syncer.client.object_delete(obj['name'])
                print("Deleted remote object '%s'" % (obj['name']))
        print("Emptied remote directory '%s'" % name)

    def local_recursive_delete(self, folder):
        """rm -rf folder"""
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        print("Emptied local directory '%s'" % folder)

    def __init__(self, syncer, local, folder = None):
        self.syncer = syncer
        self.local = local
        if folder is None:
            self.read_meta_file()
        else:
            self.folder = folder

    def clone(self):
        """Builds a new working copy by cloning a folder from a remote container."""

        print("Using account '%s' on Pithos server '%s'." %
              (self.syncer.account, self.syncer.url))
        print("Cloning folder '%s' from remote container '%s' "
              "into local directory '%s'..." %
              (self.folder, self.syncer.container, self.local))
        self.recursive_download(self.folder)
        self.write_meta_file()

    def write_meta_file(self):
        config = ConfigParser.ConfigParser()
        config.add_section('pithos')
        config.set('pithos', 'remote', self.folder)
        with open('%s/.pithos' % self.local, 'w') as f:
            config.write(f)

    def read_meta_file(self):
        config = ConfigParser.ConfigParser()
        try:
            config.read(os.path.join(self.local, '.pithos'))
        except:
            raise InvalidWorkingCopy
        self.folder = config.get('pithos', 'remote')

    def local_to_remote_path(self, root, name):
        path = os.path.join(root, name)
        native_path = path[len(self.local + os.sep):]
        remote_path = native_path.replace(os.sep, '/')
        return remote_path

    def push(self):
        self.remote_recursive_delete_contents(self.folder)
        for root, dirs, files in os.walk(self.local, topdown=False):
            for name in files:
                if root == self.local and name == '.pithos':
                    continue
                self.upload(self.local_to_remote_path(root, name),
                            os.path.join(root, name))
            for name in dirs:
                self.remote_mkdir(self.local_to_remote_path(root, name))

    def pull(self):
        self.local_recursive_delete(self.local)
        self.clone()


class Syncer:
    def __init__(self, url, token, account, container):
        self.url = url
        self.token = token
        self.account = account
        self.container = container
        self.client = PithosClient(self.url, self.token,
                                   self.account, self.container)

    def clone(self, local, folder):
        try:
            if not os.listdir(local) == []:
                raise DirectoryNotEmptyError()
        except OSError:
            try:
                print('Making local directory "%s"' % local)
                os.mkdir(local)
            except OSError:
                raise FileNotFoundError()
        # except TypeError: # if local is not a string
        working_copy = WorkingCopy(self, local, folder)
        working_copy.clone()
        return working_copy

    def working_copy(self, local):
        working_copy = WorkingCopy(self, local)
        return working_copy
