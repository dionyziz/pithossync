import time
import threading


class RemoteMetaFile:
    REMOTE_META_FILENAME = '.pithos_sync'

    def create(remote_container, remote_dir):
        upload(container: remote_container,
               name: remote_dir + '/' + self.REMOTE_META_FILENAME,
               contents: '',
               if_not_match: *)


class LocalMetaFile:
    LOCAL_META_FILENAME = '.pithos'

    def create(self, remote_server, remote_container, remote_dir, local_dir):
        # raises IOError
        meta = {
            remote_container: remote_container,
            remote_dir: remote_dir,
            remote_server: remote_server
        }
        # TODO: Write versions/dates of current files in directory
        lock_file_name = os.path.join(local_dir, self.LOCAL_META_FILENAME)
        lock_file_contents = serialize(meta)
        try:
            fd = os.open(lock_file_name, os.O_EXCL | os.O_CRETAT)
            os.write(fd, lock_file_contents)
        finally:
            os.close(fd)


def init(remote_container, remote_dir):
    RemoteMetaFile().create(remote_container, remote_dir)

class Lock:
    SLEEP_BEFORE_RETRY = 0.5 # seconds
    OBTAIN_TRIALS = 10
    KEEP_ALIVE_INTERVAL = 10 # seconds

    last_lock_str_hash = ''
    heartbeat = None

    def __init__(self):
        pass

    def __enter__(self):
        self.obtain()
        return self

    def obtain(self):
        tries = OBTAIN_TRIALS
        while tries > 0:
            contents = 'Locked.\nBy: %s\nDate: %s' % (self_id, now())
            try:
                result = upload(container: remote_container,
                                name: remote_dir + '/' + REMOTE_META_FILENAME,
                                contents: contents,
                                if_match: self.last_lock_str_hash)
                self.last_lock_str_hash = result.etag
                break
            except:
                tries -= 1
                if tries == 0:
                    break
                sleep(SLEEP_BEFORE_RETRY)

        raise Timeout

    def renew(self):
        self.obtain()

    def start_keep_alive(self):
        self.renew()
        self.heartbeat = threading.Timer(KEEP_ALIVE_INTERVAL, self.keep_alive)
        self.heartbeat.start()

    def stop_keep_alive(self):
        if self.heartbeat is not None:
            self.heartbeat.cancel()

    def __exit__(self):
        self.release()

    def release(self):
        self.stop_keep_alive()
        raise NotImplemented
        # write()

def push():
    def get_files_to_be_uploaded():
        ret = []

        for file in local_files:
            if not version match:
                raise Conflict
            if time match:
                continue
            ret.append(file)

        return ret

    def get_files_to_be_deleted():
        ret = []

        for file in remote_files:
            if file is local:
                continue
            if not version match:
                raise Conflict
            ret.append(file)

        return ret

    def upload(file):
        raise NotImplemented

    def delete(file):
        raise NotImplemented
        
    def upload_files(files_to_be_uploaded):
        for file in files_to_be_uploaded:
            upload(file)

    def delete_files(files_to_be_deleted):
        for file in files_to_be_deleted:
            delete(file)

    with Lock() as lock:
        lock.start_keep_alive()

        files_to_be_uploaded = get_files_to_be_uploaded()
        files_to_be_deleted = get_files_to_be_deleted()

        upload_files(files_to_be_uploaded)
        delete_files(files_to_be_deleted)

def clone(remote_server, remote_container, remote_dir, local_dir):
    LocalMetaFile().create(remote_server, remote_container, remote_dir, local_dir)
    pull()

def sync():
    pull()
    push()
