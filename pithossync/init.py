import logging


logger = logging.getLogger(__name__)

def init(working_copy):
    logger.info('Initing mirrored remote folder "%s" from local copy "%s"', working_copy.folder, working_copy.local)

    working_copy.remote_recursive_mkdir(working_copy.folder)
    working_copy.lock.init()
    working_copy.clone()

    logger.info("Init completed.")
