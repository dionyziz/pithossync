from kamaki.clients.pithos import PithosClient, ClientError
import os
import ConfigParser
import shutil
from pull import pull


# raised when trying to push or pull on a local directory which does not have a metafile
class InvalidWorkingCopyError(Exception):
    pass


class WorkingCopy:
    """Represents a local copy of a directory cloned from the Pithos+ server."""

    HTTP_NOT_MODIFIED = 304

    def destroy(self):
        self.delete_meta_file()

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

        # TODO: Write local meta file
        pull(self)

    def local_to_remote_path(self, root, name):
        path = os.path.join(root, name)
        native_path = path[len(self.local + os.sep):]
        remote_path = native_path.replace(os.sep, '/')

        return remote_path

    def list_objects_of_interest(self):
        ret = []

        # TODO: Use meta-file last pull date for fast pull
        if_modified_since = 'Thu, 01 Jan 1970 00:00:00 GMT'
        response = self.syncer.client.container_get(prefix=self.folder, if_modified_since=if_modified_since)

        if response.status == self.HTTP_NOT_MODIFIED:
            return {
                'modified': False
            }

        obj_list = response.json
        found = False
        for obj in obj_list:
            if obj['name'] == self.folder:
                found = True
                continue
            file = obj['name'][len(self.folder + '/'):]
            type = obj['content_type']
            ret.append(obj)
        if not found:
            raise FileNotFoundError

        return {
            'modified': True,
            'list': ret
        }

    def push(self):
        # self.remote_recursive_delete_contents(self.folder)

        obj_list = self.list_objects_of_interest()
        server_side_files = {}
        server_side_folders = {}

        constant_part = self.folder + '/'
        for obj in obj_list:
            file = obj['name'][len(constant_part):]
            type = obj['content_type']
            if self.is_folder(type):
                server_side_folders[file] = True
            else:
                server_side_files[file] = True

        # TODO: somehow mark modified files as dirty and only check their hashes
        for root, dirs, files in os.walk(self.local, topdown=False):
            for name in files:
                if root == self.local and name == '.pithos':
                    continue
                try:
                    # file already exists
                    del server_side_files[self.local_to_remote_path(root, name)]
                except:
                    pass
                # kamaki library and Pithos will take care not to upload the same file twice
                self.upload(self.local_to_remote_path(root, name),
                            os.path.join(root, name))
            for name in dirs:
                try:
                    # directory already exists
                    del server_side_folders[self.local_to_remote_path(root, name)]
                except:
                    self.remote_mkdir(self.local_to_remote_path(root, name))

        for file in server_side_files.keys() + server_side_folders.keys():
            self.syncer.client.object_delete(self.folder + '/' + file)
        print("Push successful.")

    def list_local_files(self):
        client_side_files = {}
        client_side_folders = {}

        # TODO: Push from the server to the client, or keep dirty state on the server
        for root, dirs, files in os.walk(self.local, topdown=False):
            for name in files:
                if root == self.local and pithossync.LocalMetaFile.is_meta_file(name):
                    continue
                client_side_files[self.local_to_remote_path(root, name)] = True

            for name in dirs:
                client_side_folders[self.local_to_remote_path(root, name)] = True

        return {
            'files': client_side_files,
            'folders': client_side_folders
        }

    def pull(self):
        obj_list = self.list_objects_of_interest()

        constant_part = self.folder + '/'
        for obj in obj_list:
            file = obj['name'][len(constant_part):]
            type = obj['content_type']
            if self.is_folder(type):
                try:
                    # folder already exists locally
                    del client_side_folders[file]
                except:
                    try:
                        components = file.split('/')
                        path_to_create = os.path.join(*components)
                        os.makedirs(os.path.join(self.local, path_to_create))
                        print("Created directory %s"
                              % os.path.join(self.local, file))
                    except OSError:
                        pass
            else:
                try:
                    # file already exists locally
                    del client_side_files[file]
                except:
                    pass

                components = file.split('/')
                try:
                    os.makedirs(os.path.join(self.local, *components[:-1]))
                    print("Created directory %s"
                          % os.path.join(self.local, *components[:-1]))
                except OSError:
                    pass
                # kamaki/Pithos will take care of not downloading existing files
                self.download(file)

        for file in client_side_files.keys():
            print('Removing file "%s"' % file)
            os.remove(os.path.join(self.local, file))

        for folder in client_side_folders.keys():
            print('Removing folder "%s"' % folder)
            try:
                shutil.rmtree(os.path.join(self.local, folder))
            except:
                # a parent directory may already have been removed
                pass

        print("Pull successful.")
