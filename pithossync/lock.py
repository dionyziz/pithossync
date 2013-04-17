class Lock:
    SLEEP_BEFORE_RETRY = 0.5 # seconds
    OBTAIN_TRIALS = 10
    KEEP_ALIVE_INTERVAL = 10 # seconds
    REMOTE_META_FILE = '.pithos_sync'

    last_lock_str_hash = ''
    heartbeat = None

    def __init__(self):
        pass

    def __enter__(self):
        self.obtain()
        return self

    def create(self):
        upload(container=remote_container,
               name=remote_dir + '/' + self.REMOTE_META_FILENAME,
               contents='',
               if_not_match='*')

    def obtain(self):
        tries = OBTAIN_TRIALS
        while tries > 0:
            contents = 'Locked.\nBy: %s\nDate: %s' % (self_id, now())
            try:
                result = upload(container=remote_container,
                                name=remote_dir + '/' + REMOTE_META_FILENAME,
                                contents=contents,
                                if_match=self.last_lock_str_hash)
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
