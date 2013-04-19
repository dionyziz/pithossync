import pithossync
import os
import time


def pull(working_copy):
    def list_remote_files():
        response = working_copy.list_objects_of_interest()

        if not response['modified']:
            return None

        objects = response['list']

        # handle lock
        if pithossync.Lock.exists_in(objects):
            raise pithossync.ConflictError

            # TODO: Handle pulling parallel to a pushing

            # use of that particular version of remote_meta_file is crucial, as it could have been removed and regained since
            # download_file(remote_meta_file, objects[remote_meta_file].version)
            # combine versions in remote_meta_file and list_objects

        return objects

    def download_objects(remote_object_list):
        for (name, object) in remote_object_list:
            try:
                local_version = working_copy.meta.get_object_version(object.name):

                # file has existed locally since last sync
            
                if local_version == file.version:
                    # nothing changed - we have the same version as on the server
                    # although local file may be dirty
                    continue

                # versions are strictly increasing
                assert(object.version > local_version)

                # check if local file is dirty (has modifications as compared to our local meta file)
                # TODO: Keep the hash in addition to modification date?
                stat = os.stat(object)

                if working_copy.meta.get_object_type(object.name) == 

                if time.ctime(stat.st_mtime) > working_copy.meta.get_object_modified(object.name):
                    # dirty
                    raise pithossync.ConflictError
            except:
                # file is new on the server-side
                # check if it has also been created locally
                if os.path.exists(object.name):
                    # dirty
                    raise pithossync.ConflictError

            download_file(object.name, object.version)

    def delete_files(objects):
        raise NotImplementedError

    # no lock needed for pull
    remote_file_list = list_remote_files()

    if remote_file_list is None:
        # fast pull
        return

    download_files(remote_file_list)

    local_object_list = working_copy.list_local_objects()
    local_file_list = local_object_list['files']
    local_folder_list = local_object_list['folders']

    for 

    delete_files(diff_file_list)

    # TODO: pass the appropriate file versions as they have been downloaded from the server
    #       for downloaded files and delete from the list the local files that have been deleted
    #       during this pull.
    working_copy.meta_file.update()
