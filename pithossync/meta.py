import pickle


class LocalMetaFile:
    LOCAL_META_FILENAME = '.pithos'

    remote_server = None
    remote_container = None
    remote_dir = None
    file_info = None

    local_dir = None
    meta_file_name = None

    def __init__(self, local_dir):
        self.local_dir = local_dir
        self.meta_file_name = os.path.join(self.local_dir, self.LOCAL_META_FILENAME)

    def delete(self):
        os.unlink(self.meta_file_name)

    def save(self):
        # raises IOError
        data = {
            'remote_server': self.remote_server,
            'remote_container': self.remote_container,
            'remote_dir': self.remote_dir,
            'file_info': self.file_info
        }

        # TODO: Do the pickle write using os.O_EXCL | os.O_CREAT
        with open(self.meta_file_name, 'wb') as f:
            pickle.dump(data, f)

    def load(self):
        with open(self.meta_file_name, 'rb') as f:
            data = pickle.load(f)

        self.remote_dir = data['remote_dir']
        self.remote_container = data['remote_container']
        self.remote_server = data['remote_server']
        self.file_info = data['file_info']

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
