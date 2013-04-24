import logging


logger = logging.getLogger(__name__)

def clone(working_copy):
    logger.info("Using account '%s' on Pithos server '%s'." %
                (working_copy.syncer.account, working_copy.syncer.url))
    logger.info("Cloning folder '%s' from remote container '%s' "
                "into local directory '%s'..." %
                (working_copy.folder, working_copy.syncer.container, working_copy.local))
    working_copy.meta_file.create(working_copy.syncer.url, working_copy.syncer.container, working_copy.folder)
    working_copy.pull()
    logger.info("Cloning completed.")
