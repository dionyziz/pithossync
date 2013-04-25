from kamaki.clients.pithos import PithosClient, ClientError
import os
import ConfigParser
import shutil

from init import init
from push import push
from pull import pull
from clone import clone

import meta
import lock
import logging
from pprint import pprint


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# raised when trying to push or pull on a local directory which does not have a metafile
class InvalidWorkingCopyError(Exception):
    pass


class FileNotFoundError(Exception):
    pass


class WorkingCopy:
    """Represents a local copy of a directory cloned from the Pithos+ server."""

    HTTP_NOT_MODIFIED = 304

    @staticmethod
    def is_folder(type):
        return type in ['application/directory', 'application/folder']

    def destroy(self):
        self.delete_meta_file()

    def download(self, name, version):
        remotepath = self.folder + '/' + name
        path = os.path.join(self.local, os.path.join(*name.split('/')))
        try:
            f = open(path, 'wb+')
        except:
            # TODO: make this an exception?
            logger.error("Failed to write to local file '%s'." % path)
            return
        try:
            self.client.download_object(remotepath, f)
        except ClientError:
            # TODO: make this an exception?
            logger.error("Failed to download %s." % remotepath)
            return
        f.close()
        logger.info("Downloaded remote file '%s' into %s (%i bytes)" %
                    (remotepath, path, os.stat(path).st_size))

    def upload(self, destination, source):
        f = open(source, 'r')
        self.client.upload_object(self.folder + '/' + destination, f)
        f.close()
        logger.info("Uploaded local file '%s' (%i bytes)" %
                    (source, os.stat(source).st_size))

    def remote_recursive_mkdir(self, name):
        logger.info('Creating remote directory "%s" recursively.', name)

        parts = name.split('/')

        for i, _ in enumerate(parts):
            dir = '/'.join(parts[0:i + 1])
            logger.debug('Creating remote directory "%s".' % dir)
            self.client.create_directory(dir)

    def remote_mkdir(self, name):
        dir = self.folder + '/' + name
        logger.info('Creating remote directory "%s".' % dir)
        self.client.create_directory(dir)
        logger.info('Created remote directory "%s".' % dir)

    def remote_recursive_delete_contents(self, name):
        obj_list = self.client.list_objects()
        # delete all the folders' contents
        for obj in obj_list:
            if obj['name'][0:len(name + '/')] == name + '/':
                self.client.object_delete(obj['name'])
                logger.info("Deleted remote object '%s'" % (obj['name']))
        logger.info("Emptied remote directory '%s'" % name)

    def __init__(self, syncer, local, folder = None):
        self.syncer = syncer
        self.local = local
        self.meta_file = meta.LocalMetaFile(self.local)
        self.lock = lock.Lock(self)

        self.client = PithosClient(syncer.url, syncer.token,
                                   syncer.account, syncer.container)

        if folder is None:
            # working copy already init'ed
            self.meta_file.load()
            self.folder = self.meta_file.remote_dir
        else:
            # working copy not init'ed
            # the caller must call .init() or .clone() on it
            self.folder = folder

    def init(self):
        """Builds a new local working copy by initializing a new empty remote folder"""

        init(self)

    def clone(self):
        """Builds a new local working copy by cloning a folder from an already inited
           remote folder in a container."""
        
        clone(self)

    def local_to_remote_path(self, root, name):
        path = os.path.join(root, name)
        native_path = path[len(self.local + os.sep):]
        remote_path = native_path.replace(os.sep, '/')

        return remote_path

    def list_objects_of_interest(self):
        logger.debug('Listing objects in remote folder "%s"', self.folder)

        ret = {}

        # TODO: Use meta-file last pull date for fast pull
        if_modified_since = 'Thu, 01 Jan 1970 00:00:00 GMT'
        response = self.client.container_get(prefix=self.folder, if_modified_since=if_modified_since)

        if response.status == self.HTTP_NOT_MODIFIED:
            logger.debug('Received HTTP_NOT_MODIFIED, listing suppressed.')

            return {
                'modified': False
            }

        obj_list = response.json
        found = False
        for obj in obj_list:
            logger.debug('Found remote object "%s" with content type "%s" and version %i.', obj['name'], obj['content_type'], obj['x_object_version'])

            if obj['name'] == self.folder:
                found = True
                continue
            name = obj['name'][len(self.folder + '/'):]
            is_folder = self.is_folder(obj['content_type'])
            version = obj['x_object_version']
            ret[name] = {
                'name': name,
                'is_folder': is_folder,
                'version': version
            }

        if not found:
            logger.debug('Parent directory "%s" requested not found.', self.folder)

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
            self.client.object_delete(self.folder + '/' + file)
        logger.info("Push successful.")

    def list_local_objects(self):
        client_side_files = {}
        client_side_folders = {}

        # TODO: Push from the server to the client, or keep dirty state on the server
        for root, dirs, files in os.walk(self.local, topdown=False):
            for name in files:
                if root == self.local and meta.LocalMetaFile.is_meta_file(name):
                    continue
                client_side_files[self.local_to_remote_path(root, name)] = True

            for name in dirs:
                client_side_folders[self.local_to_remote_path(root, name)] = True

        return {
            'files': client_side_files,
            'folders': client_side_folders
        }

    def pull(self):
        return pull(self)

#        obj_list = self.list_objects_of_interest()
#
#        constant_part = self.folder + '/'
#        for obj in obj_list:
#            file = obj['name'][len(constant_part):]
#            type = obj['content_type']
#            if self.is_folder(type):
#                try:
#                    # folder already exists locally
#                    del client_side_folders[file]
#                except:
#                    try:
#                        components = file.split('/')
#                        path_to_create = os.path.join(*components)
#                        os.makedirs(os.path.join(self.local, path_to_create))
#                        print("Created directory %s"
#                              % os.path.join(self.local, file))
#                    except OSError:
#                        pass
#            else:
#                try:
#                    # file already exists locally
#                    del client_side_files[file]
#                except:
#                    pass
#
#                components = file.split('/')
#                try:
#                    os.makedirs(os.path.join(self.local, *components[:-1]))
#                    print("Created directory %s"
#                          % os.path.join(self.local, *components[:-1]))
#                except OSError:
#                    pass
#                # kamaki/Pithos will take care of not downloading existing files
#                self.download(file)
#
#        for file in client_side_files.keys():
#            print('Removing file "%s"' % file)
#            os.remove(os.path.join(self.local, file))
#
#        for folder in client_side_folders.keys():
#            print('Removing folder "%s"' % folder)
#            try:
#                shutil.rmtree(os.path.join(self.local, folder))
#            except:
#                # a parent directory may already have been removed
#                pass
#
#        print("Pull successful.")
