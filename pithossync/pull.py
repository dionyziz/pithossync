import pithossync
import os
import time
import shutil


def pull(working_copy):
    local = working_copy.local

    def list_remote_objects():
        response = working_copy.list_objects_of_interest()

        if not response['modified']:
            return None

        objects = response['list']

        # handle lock
        if working_copy.lock.active_in(working_copy.lock.extract_from(objects)):
            raise pithossync.ConflictError

            # TODO: Handle pulling parallel to a pushing

            # use of that particular version of remote_meta_file is crucial, as it could have been removed and regained since
            # download_file(remote_meta_file, objects[remote_meta_file].version)
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
            working_copy.meta.get_object_version(object_path)

            # check that object also exists locally
            if not os.path.exists(os_path):
                return CLEANLINESS_CLEAN
            
            # check if currently is a dir
            if os.path.isdir(local_object_path):
                # was also a dir in last pull?
                if working_copy.meta.is_object_folder(object_path):
                    return CLEANLINESS_CLEAN

            # object locally is a file
            # check that it was a file in last pull
            if not working_copy.meta.is_object_file(object_path):
                # object was not a file in last pull
                return CLEANLINESS_DIRTY_TYPE_CHANGED

            # object was and is a file
            # get its details
            stat = os.stat(local_object_path)

            # TODO: if mtimes match, compare hashes
            present_time = time.ctime(stat.st_mtime)
            past_time = working_copy.meta.get_object_modified(object_path)

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
        for object in remote_object_list:
            try:
                # throws
                local_version = working_copy.meta.get_object_version(object.name)

                # file has existed locally since last sync
            
                if local_version == file.version:
                    # nothing changed - we have the same version as on the server
                    # although local file may be dirty
                    continue

                # versions are strictly increasing
                assert(object.version > local_version)

                if is_object_dirty(object.name):
                    raise pithossync.ConflictError

            except KeyError:
                # file is new on the server-side
                # check if it has also been created locally
                
                # check if folder
                if object.folder and os.isdir(object.name):
                    # remote object is a folder and has also been created locally as a folder
                    # nothing to do
                    continue

                if is_object_dirty(object.name):
                    raise pithossync.ConflictError

            if object.folder:
                try:
                    os.makedirs(object.name)
                except OSError:
                    # directory already exists; this is caused if it was created as a parent directory previously
                    pass

                # modified date does not matter for folders
                working_copy.meta.set_file_version(object.name, object.version)
            else:
                try:
                    os.makedirs(os.path.dirname(object.name))
                except OSError:
                    pass

                download_file(object.name, object.version)

                # We are assuming that the user is not modifying any files while the pull operation is running
                stat = os.stat(local_object_path)
                present_time = time.ctime(stat.st_mtime)

                working_copy.meta.set_file_modified(object.name, present_time)
                working_copy.meta.set_file_version(object.name, object.version)

    def delete_objects(objects):
        # TODO: Remove all files first and then folders from leafs to root
        #       and assert that rmdirs are successful (unless they are CLEANLINESS_DIRTY_DELETED)

        for object in objects:
            if get_local_object_cleanliness(object.name) not in [CLEANLINESS_DIRTY_DELETED, CLEANLINESS_CLEAN]:
                raise pithossync.ConflictError
            shutil.rmtree(os.path.join(self.local, folder))
            working_copy.meta.remove_object(object)

    # no lock needed for pull
    remote_file_list = list_remote_objects()

    if remote_file_list is None:
        # fast pull
        return

    local_object_list = working_copy.meta.get_object_list()

    download_objects(remote_file_list)

    # TODO: unify formats for local/remote file lists

    for name in local_object_list.keys():
        if name in remote_file_list:
            del local_object_list[local_object_list[name]]

    delete_objects(local_object_list)

    # TODO: pass the appropriate file versions as they have been downloaded from the server
    #       for downloaded files and delete from the list the local files that have been deleted
    #       during this pull.
    # working_copy.meta_file.update()
