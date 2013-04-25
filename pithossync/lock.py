import uuid
import tempfile
import os
import logging
import sys


logger = logging.getLogger(__name__)


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

    @classmethod
    def is_lock_file(cls, name):
        return cls.REMOTE_META_FILE == name

    def __init__(self, working_copy):
        self.working_copy = working_copy
        self.client_id = uuid.uuid4()

    def __enter__(self):
        logger.debug('Entering lock critical section.')
        self.obtain()
        return self

    def __exit__(self):
        logger.debug('Leaving lock critical section.')
        self.release()

    def exists_in(self, object_list):
        return Lock.REMOTE_META_FILE in object_list

    def extract_from(self, base_path, object_list):
        # TODO: delegate downloading to WorkingCopy?
        # raises KeyError if lock does not exist

        (fh, name) = tempfile.mkstemp()
        file = os.fdopen(fh, 'wb')

        lock_file = object_list[Lock.REMOTE_META_FILE]

        logger.debug('Downloading lock file "%s" at version %i.', lock_file['name'], lock_file['version'])
        self.working_copy.syncer.client.download_object(base_path + '/' + lock_file['name'], file, version=lock_file['version'])
        logger.debug('Download successful.')

        file.close()

        with open(name) as f:
            lock_data = f.read()

        os.unlink(name)

        return lock_data

    def active_in(self, data):
        # TODO: Handle multiple locks here
        return data != ''


    # TODO: get the versions of the files that are locked by the pusher

    def put(self, contents, create):
        # contents = 'Locked: Yes\nClient: %s\nAutoincrement: %i' % (self.client_id, self.autoincrement)
        logger.debug('Updating lock file on the server.')

        # TODO: put data directly to Pithos when kamaki supports this, without writing it to a file first
        (fh, name) = tempfile.mkstemp()
        file = os.fdopen(fh, 'w')
        file.write(contents)
        file.close()

        with open(name) as f:
            # TODO: if not modified since etc.
            # TODO: upload using working_copy instead of accessing the syncer directly?
            lock_name = self.working_copy.folder + '/' + self.REMOTE_META_FILE
            if create:
                logger.debug('Creating new lock file on the server.')
                # make sure using 'if_not_match: *' that nobody else is creating the lock file
                self.working_copy.syncer.client.upload_object(lock_name, f, if_not_exist=True)
                # TODO: handle lock created in the meantime race-condition
            else:
                logger.debug('Updating existing lock file on the server.')
                self.working_copy.syncer.client.upload_object(lock_name, f, if_etag_match=self.last_lock_str_hash)
                # TODO: handle lock modified by someone else (in case of multilocking)

        os.unlink(name)

        # TODO: when kamaki supports etag retrieval, change this to read from the upload result
        self.last_lock_str_hash = 'I am an etag'
        self.autoincrement += 1

        logger.debug('Lock update successful.')

    def init(self):
        logger.debug('Initing lock.')

        self.put('', True)

        logger.debug('Lock init successful.')

    def obtain(self):
        logger.debug('Obtaining lock as client %s with autoincrement %s.' % (self.client_id, self.autoincrement))

        tries = self.OBTAIN_TRIALS
        while tries > 0:
            # TODO: Use self.put
            contents = 'Locked.\nBy: %s\nAutoincrement: %s' % (self.client_id, self.autoincrement)
            try:
                result = self.put(contents, False)
                logger.debug('Lock obtained successfully.')
                break
            except:
                logger.debug('Failed to obtain lock.')
                tries -= 1
                if tries == 0:
                    logger.warning('Failed to obtain lock and timed out. Bailing out.')
                    break
                logger.debug('Retrying to obtain lock after %i.' % self.SLEEP_BEFORE_RETRY)
                sleep(self.SLEEP_BEFORE_RETRY)

        raise TimeoutError

    def renew(self):
        raise NotImplementedError

    def start_keep_alive(self):
        logger.debug('Lock heartbeat.')
        self.renew()
        self.heartbeat = threading.Timer(self.KEEP_ALIVE_INTERVAL, self.keep_alive)
        self.heartbeat.start()
        logger.debug('Heartbeat completed.')

    def stop_keep_alive(self):
        if self.heartbeat is not None:
            self.heartbeat.cancel()

    def release(self):
        logger.debug('Releasing lock.')
        self.stop_keep_alive()
        raise NotImplementedError
        # write()
