import pithossync
import os
import time
import shutil
import logging
from lock import Lock


logger = logging.getLogger(__name__)

def pull(working_copy):
    local = working_copy.local

    def list_remote_objects():
        response = working_copy.list_objects_of_interest()

        if not response['modified']:
            return None

        objects = response['list']

        # handle lock
        if working_copy.lock.active_in(working_copy.lock.extract_from(working_copy.folder, objects)):
            raise pithossync.ConflictError

            # TODO: Handle pulling parallel to a pushing

            # use of that particular version of remote_meta_file is crucial, as it could have been removed and regained since
            # download_file(remote_meta_file, objects[remote_meta_file]['version'])
            # combine versions in remote_meta_file and list_objects

        return objects

    CLEANLINESS_CLEAN = 0
    CLEANLINESS_DIRTY_CREATED = 1
    CLEANLINESS_DIRTY_DELETED = 2
    CLEANLINESS_DIRTY_TYPE_CHANGED = 3
    CLEANLINESS_DIRTY_MODIFIED = 4

    def get_local_object_cleanliness(object_path):
        local_object_path = os.path.join(local, object_path)

        try:
            # check that object existed in last pull
            working_copy.meta_file.get_object_version(object_path)

            # check that object also exists locally
            if not os.path.exists(os_path):
                return CLEANLINESS_DIRTY_DELETED
            
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
                    return CLEANLINESS_CLEAN

            # object locally is a file
            # check that it was a file in last pull
            if not working_copy.meta_file.is_object_file(object_path):
                # object was not a file in last pull
                return CLEANLINESS_DIRTY_TYPE_CHANGED

            # object was and is a file
            # get its details
            stat = os.stat(local_object_path)

            # TODO: if mtimes match, compare hashes
            present_time = time.ctime(stat.st_mtime)
            past_time = working_copy.meta_file.get_object_modified(object_path)

            assert(present_time >= past_time)

            if present_time != past_time:
                return CLEANLINESS_DIRTY_MODIFIED

            return CLEANLINESS_CLEAN

        except KeyError:
            # since we have an exception, object did not exist in last pull
            # check if it exists now
            if os.path.exists(local_object_path):
                return CLEANLINESS_DIRTY_CREATED

            # file did not exist in last pull and does not exist now either
            return CLEANLINESS_CLEAN

    def is_local_object_dirty(object_path):
        return get_local_object_cleanliness(object_path) != CLEANLINESS_CLEAN

    def download_file(object_name, object_version):
        working_copy.download(object_name, version=object_version)

    def download_objects(remote_object_list):
        logger.debug('Processing %i remote objects', len(remote_object_list))

        # TODO: Sort remote_object_list by path length in ascending order
        #       so that directories can be created incrementally without
        #       being interpreted as dirty.

        for (name, object) in remote_object_list.items():
            logger.debug('Processing remote object "%s" at version %i', object['name'], object['version'])

            if Lock.is_lock_file(name):
                logger.debug('Skipping server lock file.')
                continue

            try:
                # throws
                local_version = working_copy.meta_file.get_object_version(object['name'])

                logger.debug('Object exists locally since last pull.')

                # file has existed locally since last sync
            
                if local_version == object['version']:
                    # nothing changed - we have the same version as on the server
                    # although local file may be dirty
                    logger.debug('Local object version %i and remote object version %i match, no download needed.', local_version, object['version'])
                    continue

                # versions are strictly increasing
                assert(object['version'] > local_version)

                logger.debug('Local object version %i is outdated and superseeded by remote object version %i.', local_version, object['version'])

                if is_object_dirty(object['name']):
                    logger.debug('Local object is dirty, bailing out with conflict.')
                    raise pithossync.ConflictError

                # TODO: remove object from local storage before downloading it / mkdiring it
                #       as it might be of different type

            except KeyError:
                # file is new on the server-side
                # check if it has also been created locally

                logger.debug('Object is new since last pull.')
                
                # check if folder
                if object['is_folder'] and os.isdir(object['name']):
                    logger.debug('Remote object is a folder and has also been created locally, no action needed.')

                    # remote object is a folder and has also been created locally as a folder
                    # nothing to do
                    continue

                if is_object_dirty(object['name']):
                    logger.debug('Object has also been created independently locally, bailing out with conflict.')

                    raise pithossync.ConflictError

            if object['folder']:
                logger.debug('Remote object is a folder.')
                
                try:
                    logger.debug('makedirs "%s"', object['name'])

                    os.makedirs(object['name'])

                    logger.debug('mkdir successful.')
                except OSError:
                    logger.debug('mkdir failed.')

                    # directory already exists; this is caused if it was created as a parent directory previously
                    pass

                logger.debug('Updating meta file with new folder object information.')

                # modified date does not matter for folders
                working_copy.meta_file.set_file_version(object['name'], object['version'])

                logger.debug('Meta file updated.')
            else:
                logger.debug('Remote object is a file.')

                try:
                    os.makedirs(os.path.dirname(object['name']))
                    logger.debug('Created parent directories of "%s".', object['name'])
                except OSError:
                    pass

                logger.debug('Downloading remote file object "%s" at version %i.', object['name'], object['version'])

                download_file(object['name'], object['version'])

                logger.debug('File object downloaded.')

                # We are assuming that the user is not modifying any files while the pull operation is running
                stat = os.stat(local_object_path)
                present_time = time.ctime(stat.st_mtime)

                logger.debug('Updating meta file with new file object information.')

                working_copy.meta_file.set_file_modified(object['name'], present_time)
                working_copy.meta_file.set_file_version(object['name'], object['version'])

                logger.debug('Meta file updated.')

        logger.debug('%i remote objects processed.', len(remote_object_list))

    def delete_objects(objects):
        # TODO: Remove all files first and then folders from leafs to root
        #       and assert that rmdirs are successful (unless they are CLEANLINESS_DIRTY_DELETED)

        logger.debug('Deleting %i objects', len(objects))

        for object in objects:
            logger.debug('Deleting object "%s"', object['name'])
            if get_local_object_cleanliness(object['name']) not in [CLEANLINESS_DIRTY_DELETED, CLEANLINESS_CLEAN]:
                raise pithossync.ConflictError
            shutil.rmtree(os.path.join(self.local, folder))
            working_copy.meta_file.remove_object(object)

        logger.debug('%i objects deleted.', len(objects))

    logger.info('Pulling remote mirrored folder "%s" into local working copy "%s"', working_copy.folder, working_copy.local)

    # no lock needed for pull
    remote_object_list = list_remote_objects()

    if remote_object_list is None:
        # fast pull
        return

    local_object_list = working_copy.meta_file.get_object_list()

    download_objects(remote_object_list)

    # TODO: unify formats for local/remote file lists

    for name in local_object_list.keys():
        if name in remote_file_list:
            del local_object_list[local_object_list[name]]

    delete_objects(local_object_list)

    # TODO: pass the appropriate file versions as they have been downloaded from the server
    #       for downloaded files and delete from the list the local files that have been deleted
    #       during this pull.
    # working_copy.meta_file.update()

    logger.info('Pull successful.')
