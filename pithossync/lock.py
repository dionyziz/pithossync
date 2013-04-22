import uuid
import tempfile
import os


class TimeoutError(Exception):
    pass


class LockViolationError(Exception):
    pass


# TODO: Add support for multiple locks at the same time
# TODO: Create instant of 'past lock' from data/filelist/(name and version)
class Lock:
    SLEEP_BEFORE_RETRY = 0.5 # seconds
    OBTAIN_TRIALS = 10
    KEEP_ALIVE_INTERVAL = 10 # seconds
    REMOTE_META_FILE = '.pithos_sync'

    last_lock_str_hash = None
    heartbeat = None

    working_copy = None
    client_id = None
    autoincrement = 0

    def __init__(self, working_copy):
        self.working_copy = working_copy
        self.client_id = uuid.uuid4()

    def __enter__(self):
        self.obtain()
        return self

    def exists_in(self, object_list):
        return Lock.REMOTE_META_FILE in object_list

    def extract_from(self, object_list):
        # TODO: delegate downloading to WorkingCopy?
        # raises KeyError if lock does not exist

        (fh, name) = tempfile.mkstemp()
        file = os.fdopen(fh)
        file.close()

        lock_file = object_list[Lock.REMOTE_META_FILE]
        self.working_copy.syncer.client.download_object(lock_file.name, file, version=lock_file.version)

        os.unlink(name)

        with open(name) as f:
            return f.read()

    def active_in(self, data):
        # TODO: Handle multiple locks here
        return data != ''


    # TODO: get the versions of the files that are locked by the pusher

    def put(self):
        contents = 'Locked: Yes\nClient: %s\nAutoincrement: %i' % (self.client_id, self.autoincrement)

        # TODO: put data directly to Pithos when kamaki supports this, without writing it to a file first
        (fh, name) = tempfile.mkstemp()
        file = os.fdopen(fh, 'w')
        file.write(contents)
        file.close()

        # TODO: if not modified since etc.
        # TODO: delegate uploading to WorkingCopy?
        self.working_copy.syncer.client.upload_object(working_copy.folder + '/' + self.REMOTE_META_FILE, file)
        os.unlink(name)

    def init(self):
        # TODO: Use self.put
        upload(container=remote_container,
               name=remote_dir + '/' + self.REMOTE_META_FILENAME,
               contents='',
               if_not_match='*')

    def obtain(self):
        tries = self.OBTAIN_TRIALS
        while tries > 0:
            # TODO: Use self.put
            contents = 'Locked.\nBy: %s\nAutoincrement: %s' % (self.client_id, self.autoincrement)
            try:
                result = upload(container=remote_container,
                                name=remote_dir + '/' + REMOTE_META_FILENAME,
                                contents=contents,
                                if_match=self.last_lock_str_hash)
                self.last_lock_str_hash = result.etag
                self.autoincrement += 1
                break
            except:
                tries -= 1
                if tries == 0:
                    break
                sleep(self.SLEEP_BEFORE_RETRY)

        raise TimeoutError

    def renew(self):
        raise NotImplementedError

    def start_keep_alive(self):
        self.renew()
        self.heartbeat = threading.Timer(self.KEEP_ALIVE_INTERVAL, self.keep_alive)
        self.heartbeat.start()

    def stop_keep_alive(self):
        if self.heartbeat is not None:
            self.heartbeat.cancel()

    def __exit__(self):
        self.release()

    def release(self):
        self.stop_keep_alive()
        raise NotImplementedError
        # write()
