import pickle
import os
import copy
import logging


logger = logging.getLogger(__name__)


class LocalMetaFile:
    LOCAL_META_FILENAME = '.pithos'

    pickled_keys = ['remote_server',
                    'remote_container',
                    'remote_dir',
                    'object_info',
                    'empty_lock_file_hash']

    remote_server = None
    remote_container = None
    remote_dir = None
    object_info = None
    empty_lock_file_hash = None

    local_dir = None
    meta_file_name = None

    @classmethod
    def is_meta_file(name):
        return LocalMetaFile.LOCAL_META_FILENAME == name

    def __init__(self, local_dir):
        self.local_dir = local_dir
        self.meta_file_name = os.path.join(self.local_dir, self.LOCAL_META_FILENAME)

    def create(self, remote_server, remote_container, remote_dir):
        logger.debug('Creating new local meta file in directory "%s" for remote url "%s" using container "%s" and remote directory "%s"',
                     self.local_dir, remote_server, remote_container, remote_dir)

        self.remote_server = remote_server
        self.remote_container = remote_container
        self.remote_dir = remote_dir
        self.save()

        logger.debug('Local meta file created.')

    def delete(self):
        logger.debug('Deleting local meta file "%s"', self.meta_file_name)

        os.unlink(self.meta_file_name)

        logger.debug('Meta file deleted.')

    def save(self):
        logger.debug('Saving local meta file as "%s"', self.meta_file_name)

        try:
            # raises IOError
            data = {}

            for key in self.pickled_keys:
                data[key] = getattr(self, key)

            # TODO: Do the pickle write using os.O_EXCL | os.O_CREAT
            with open(self.meta_file_name, 'wb') as f:
                pickle.dump(data, f)

            logger.debug('Meta file saved.')
        except IOError as e:
            logger.warning('Failed to create local meta file.')
            raise e

    def load(self):
        logger.debug('Loading local meta file from path "%s"', self.meta_file_name)

        with open(self.meta_file_name, 'rb') as f:
            data = pickle.load(f)

        for (key, value) in data.items():
            if key not in self.pickledkeys:
                # meta file is broken
                raise ValueError
            setattr(self, key, value)

        logger.debug('Meta file loaded.')

    # all object paths are relative to the root/local directory of the working copy
    def get_object_version(self, path):
        return self.object_info[path].version

    def set_object_version(self, path, version):
        if path not in self.object_info:
            self.object_info[path] = {}
        self.object_info[path].version = version

    def get_file_modified(self, path):
        assert(not self.object_info[path].folder)
        return self.object_info[path].modified

    def set_file_modified(self, path, date):
        if path not in self.object_info:
            self.object_info[path] = {}
        assert(not self.object_info[path].folder)
        self.object_info[path].modified = date

    def is_object_folder(self, path):
        return self.object_info[path].folder
    
    def is_object_file(self, path):
        return not self.object_info[path].folder

    def mark_object_as_folder(self, path):
        if path not in self.object_info:
            self.object_info[path] = {}
        self.object_info[path].folder = True

    def mark_object_as_file(self, path):
        if path not in self.object_info:
            self.object_info[path] = {}
        self.object_info[path].folder = False

    def remove_object(self, path):
        del self.object_info[path]

    def get_object_list(self):
        return copy.deepcopy(self.object_info)
