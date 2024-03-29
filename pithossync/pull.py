import pithossync
import os
import time
import shutil
import logging
from lock import Lock
import dirty


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

            # TODO: Handle pulling parallel to a push

            # use of that particular version of remote_meta_file is crucial, as it could have been removed and regained since
            # download_file(remote_meta_file, objects[remote_meta_file]['version'])
            # combine versions in remote_meta_file and list_objects

        return objects

    def download_file(object_name, object_version):
        working_copy.download(object_name, version=object_version)

    def filter_objects_to_download(remote_object_list):
        filtered_object_list = {}

        logger.debug('Filtering %i remote objects to download.', len(remote_object_list))

        for (name, object) in remote_object_list.items():
            logger.debug('Processing remote object "%s" at version %i.', object['name'], object['version'])

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

                if dirty.is_local_object_dirty(working_copy, object['name']):
                    logger.debug('Local object is dirty, bailing out with conflict.')
                    raise pithossync.ConflictError
            except KeyError:
                # file is new on the server-side
                # check if it has also been created locally

                logger.debug('Object is new since last pull.')
                
                # check if folder
                if object['is_folder'] and os.path.isdir(object['name']):
                    logger.debug('Remote object is a folder and has also been created locally, no action needed.')

                    # remote object is a folder and has also been created locally as a folder
                    # nothing to do
                    continue

                if dirty.is_local_object_dirty(working_copy, object['name']):
                    logger.debug('Object has also been created independently locally, bailing out with conflict.')

                    raise pithossync.ConflictError

            if object['is_folder']:
                type = 'folder'
            else:
                type = 'file'

            logger.debug('Queueing remote object of type %s named "%s" at version "%i" to be fetched.', type, object['name'], object['version'])

            filtered_object_list[object['name']] = object

        logger.debug('%i remote objects filtered down to %i.', len(remote_object_list), len(filtered_object_list))

        return filtered_object_list

    def download_objects(remote_object_list):
        logger.debug('Fetching %i remote objects.', len(remote_object_list))

        for (name, object) in remote_object_list.items():
            logger.debug('Fetching remote object "%s" at version %i.', object['name'], object['version'])

            # TODO: remove object from local storage before downloading it / mkdiring it
            #       as it might be of different type

            if object['is_folder']:
                logger.debug('Remote object is a folder.')
                
                try:
                    logger.debug('makedirs "%s"', object['name'])

                    os.makedirs(working_copy.local + '/' + object['name'])

                    logger.debug('mkdir successful.')
                except OSError:
                    # directory already exists; this is caused if it was created as a parent directory previously
                    logger.debug('mkdir failed.')

                logger.debug('Updating meta file with new folder object information.')

                working_copy.meta_file.mark_object_as_folder(object['name'])
                # modified date does not matter for folders
                working_copy.meta_file.set_object_version(object['name'], object['version'])

                logger.debug('Meta file updated.')
            else:
                logger.debug('Remote object is a file.')

                try:
                    os.makedirs(working_copy.local + '/' + os.path.dirname(object['name']))
                    logger.debug('Created parent directories of "%s".', object['name'])
                except OSError:
                    pass

                logger.debug('Downloading remote file object "%s" at version %i.', object['name'], object['version'])

                download_file(object['name'], object['version'])

                logger.debug('File object downloaded.')

                # We are assuming that the user is not modifying any files while the pull operation is running
                stat = os.stat(working_copy.local + '/' + object['name'])
                present_time = time.ctime(stat.st_mtime)

                logger.debug('Updating meta file with new file object information.')

                working_copy.meta_file.mark_object_as_file(object['name'])
                working_copy.meta_file.set_file_modified(object['name'], present_time)
                working_copy.meta_file.set_object_version(object['name'], object['version'])

                logger.debug('Meta file updated.')

        logger.debug('%i remote objects fetched.', len(remote_object_list))

    def delete_objects(objects):
        # TODO: Remove all files first and then folders from leafs to root
        #       and assert that rmdirs are successful (unless they are DELETED)

        logger.debug('Deleting %i objects', len(objects))

        for object in objects:
            logger.debug('Deleting object "%s"', object['name'])
            if dirty.get_local_object_cleanliness(object['name']) not in [dirty.DELETED, dirty.CLEAN]:
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

    filtered_remote_object_list = filter_objects_to_download(remote_object_list)
    local_object_list = working_copy.meta_file.get_object_list()

    logger.debug('About to apply local changes!')

    download_objects(filtered_remote_object_list)

    # TODO: unify formats for local/remote file lists

    for name in local_object_list.keys():
        if name in remote_object_list:
            del local_object_list[name]

    delete_objects(local_object_list)

    # TODO: pass the appropriate file versions as they have been downloaded from the server
    #       for downloaded files and delete from the list the local files that have been deleted
    #       during this pull.
    working_copy.meta_file.save()

    logger.info('Pull successful.')
