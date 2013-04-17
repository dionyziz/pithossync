def pull(working_copy):
    def list_files(prefix):
        response = working_copy.list_objects_of_interest(prefix=prefix, if_modified_since=last_server_container_modified)

        if response.status == 302:
            return None

        objects = response.objects

        # handle lock
        if remote lock exists:
            # use of that particular version of remote_meta_file is crucial, as it could have been removed and regained since
            download_file(remote_meta_file, objects[remote_meta_file].version)
            combine versions in remote_meta_file and list_objects
        else:
            use versions in list_objects

        return list_of_objects_with_versions

    def download_files(prefix):
        for object in objects:
            if object.name in local_version:
                if local_version[object.name] == remote_version[object.name]:
                    continue
                assert(remote_version[object.name] > local_version[object.name])
                if local_dirty[object.name]:
                    raise Conflict
            else:
                if local_dirty[object.name]:
                    raise Conflict
            # it is crucial
            download_file(object.name, object.version)

    def delete_files():
        raise NotImplementedError

    # no lock needed for pull
    file_list = list_files(working_copy.folder + '/')
    if file_list is None:
        # fast pull
        return

    download_files(file_list)
    delete_files(file_list)

    update local meta file
