import pickle


class LocalMetaFile:
    LOCAL_META_FILENAME = '.pithos'

    pickled_keys = ['remote_server',
                    'remote_container',
                    'remote_dir',
                    'file_info',
                    'empty_lock_file_hash']

    remote_server = None
    remote_container = None
    remote_dir = None
    file_info = None
    empty_lock_file_hash = None

    local_dir = None
    meta_file_name = None

    def __init__(self, local_dir):
        self.local_dir = local_dir
        self.meta_file_name = os.path.join(self.local_dir, self.LOCAL_META_FILENAME)

    def delete(self):
        os.unlink(self.meta_file_name)

    def save(self):
        # raises IOError
        data = {}

        for key in self.pickled_keys:
            data[key] = getattr(self, key)

        # TODO: Do the pickle write using os.O_EXCL | os.O_CREAT
        with open(self.meta_file_name, 'wb') as f:
            pickle.dump(data, f)

    def load(self):
        with open(self.meta_file_name, 'rb') as f:
            data = pickle.load(f)

        for (key, value) in data.items():
            if key not in self.pickledkeys:
                # meta file is broken
                raise ValueError
            setattr(self, key, value)

    def get_file_version(self, path):
        return self.file_info[path].version

    def set_file_version(self, path, version):
        if path not in self.file_info:
            self.file_info[path] = {}
        self.file_info[path].version = version

    def get_file_modified(self, path):
        return self.file_info[path].modified

    def set_file_modified(self, path, date):
        if path not in self.file_info:
            self.file_info[path] = {}
        self.file_info[path].modified= date
