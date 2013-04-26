import os
import time
import logging

logger = logging.getLogger(__name__)

# clean state
CLEAN = 0

# dirty state
CREATED = 1
DELETED = 2
TYPE_CHANGED = 3
MODIFIED = 4

def get_local_object_cleanliness(working_copy, object_path):
    logger.debug('Determining object cleanliness for local object "%s".', object_path)

    local = working_copy.local
    local_object_path = os.path.join(local, object_path)

    try:
        # check that object existed in last pull
        working_copy.meta_file.get_object_version(object_path)
    except KeyError:
        # since we have an exception, object did not exist in last pull
        # check if it exists now
        if os.path.exists(local_object_path):
            logger.debug('Object "%s" is dirty: It has been created.', local_object_path)
            return CREATED

        # file did not exist in last pull and does not exist now either
        logger.debug('Object is clean: It does not exist.')
        return CLEAN

    # object has existed since last pull

    # check that object also exists locally
    if not os.path.exists(local_object_path):
        logger.debug('Object is dirty: It was deleted.')
        return DELETED
    
    # check if currently is a dir
    if os.path.isdir(local_object_path):
        # was also a dir in last pull?
        if working_copy.meta_file.is_object_folder(object_path):
            # TODO: Recursively check that the folder's contents
            #       have not been modified through creation of new objects,
            #       deletion of objects, or modification of objects
            #       such as content change or renames
            #       and return CLEANLINESS_DIRTY_MODIFIED
            #       as appropriate
            logger.debug('Object is clean: It is a folder.')
            return CLEAN

    # object locally is a file
    # check that it was a file in last pull
    if not working_copy.meta_file.is_object_file(object_path):
        # object was not a file in last pull
        logger.debug('Object is dirty: It was changed from a folder to a file.')
        return TYPE_CHANGED

    # object was and is a file
    # get its details
    stat = os.stat(local_object_path)

    # TODO: if mtimes match, compare hashes
    present_time = time.ctime(stat.st_mtime)
    past_time = working_copy.meta_file.get_file_modified(object_path)

    assert(present_time >= past_time)

    if present_time != past_time:
        logger.debug('Object is dirty: Modification times do not match.')
        return MODIFIED

    logger.debug('Object is clean.')
    return CLEAN

def is_local_object_dirty(working_copy, object_path):
    return get_local_object_cleanliness(working_copy, object_path) != CLEAN
