from kamaki.clients.pithos import PithosClient, ClientError
import os

class DirectoryNotEmptyError(Exception):
    pass

class FileNotFoundError(Exception):
    pass

class WorkingCopy:
    def download(self, name):
        remotepath = self.folder + '/' + name
        path = os.path.join(self.local, name)
        try:
            f = open(path, 'wb+')
        except:
            print("Failed to write to local file '%s'." % path)
        try:
            self.syncer.client.download_object(remotepath, f)
        except ClientError:
            print("Failed to download %s." % remotepath)
        f.close()
        print("Downloaded remote file '%s' into %s (%i bytes)" % (remotepath, path, os.stat(path).st_size))

    def upload(self, destination, source):
        f = open(source, 'r')
        self.syncer.client.upload_object(self.folder + '/' + destination, f)
        f.close()
        print("Uploaded local file '%s' (%i bytes)" % (source, os.stat(source).st_size))

    def remote_mkdir(self, name):
        dir = self.folder + '/' + name
        self.syncer.client.create_directory(dir)
        print("Created remote directory '%s'." % dir)

    def recursive_download(self, name):
        obj_list = self.syncer.client.list_objects()
        count_objects = 0
        for obj in obj_list:
            file = obj['name']
            type = obj['content_type']
            if file[0:len(name + '/')] == name + '/':
                path_after_folder = file[len(name + '/'):]
                count_objects += 1
                if type == 'application/directory' or type == 'application/folder':
                    try:
                        os.makedirs(os.path.join(self.local, path_after_folder))
                        print("Created directory %s" % os.path.join(self.local, path_after_folder))
                    except OSError:
                        pass
                components = path_after_folder.split('/')
                try:
                    os.makedirs(os.path.join(self.local, *components[:-1]))
                    print("Created directory %s" % os.path.join(self.local, *components[:-1]))
                except OSError:
                    pass
                self.download(file[len(name + '/'):])
        print("Cloning successful.")
        print("Created %i local objects out of %i total objects in container." % (count_objects, len(obj_list)))

    def remote_recursive_delete_contents(self, name):
        obj_list = self.syncer.client.list_objects()
        # delete all the folders' contents
        for obj in obj_list:
            if obj['name'][0:len(name + '/')] == name + '/':
                self.syncer.client.object_delete(obj['name'])
                print("Deleted remote object '%s'" % (obj['name']))
        print("Emptied remote directory '%s'" % (name))

    def __init__(self, syncer, local, folder):
        self.syncer = syncer
        self.local = local
        self.folder = folder

    def clone(self):
        print("Using account '%s' on Pithos server %s." %
              (self.syncer.account, self.syncer.url))
        print("Cloning folder %s from remote container %s into local directory '%s'..." %
              (self.folder, self.syncer.container, self.local))
        self.recursive_download(self.folder)

    def push(self):
        self.remote_recursive_delete_contents(self.folder)
        for root, dirs, files in os.walk(self.local, topdown=False):
            for name in files:
                path = os.path.join(root, name)
                path_after_folder = path[len(self.local + os.sep):].replace(os.sep, '/')
                self.upload(path_after_folder, os.path.join(root, name))
            for name in dirs:
                path = os.path.join(root, name)
                path_after_folder = path[len(self.local + os.sep):].replace(os.sep, '/')
                self.remote_mkdir(path_after_folder)

    def pull(self):
        pass

class Syncer:
    def __init__(self, url, token, account, container):
        self.url = url
        self.token = token
        self.account = account
        self.container = container
        self.client = PithosClient(self.url, self.token, self.account, self.container)

    def clone(self, local, folder):
        try:
            if not os.listdir(local) == []:
                raise DirectoryNotEmptyError()
        except OSError:
            raise FileNotFoundError()
        workingCopy = WorkingCopy(self, local, folder)
        workingCopy.clone()
        return workingCopy

    def workingCopy(self, local, folder):
        # TODO: use meta-data to automatically determine remote from local
        workingCopy = WorkingCopy(self, local, folder)
        return workingCopy
