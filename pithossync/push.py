import logging


def push():
    def get_files_to_be_uploaded(local_file_list, remote_file_list):
        ret = []

        for (name, file) in local_file_list.items():
            if file.version != remote_file_list[name].version:
                raise Conflict
            if not file.dirty:
                continue
            ret.append(file)

        return ret

    def get_files_to_be_deleted(local_file_list, remote_file_list):
        ret = []

        for (name, file) in remote_file_list.items():
            if file is local:
                continue
            if file.version != local_file_list[name].version:
                raise Conflict
            ret.append(file)

        return ret

    def upload(file):
        raise NotImplementedError

    def delete(file):
        raise NotImplementedError
        
    def upload_files(files_to_be_uploaded):
        for file in files_to_be_uploaded:
            upload(file)

    def delete_files(files_to_be_deleted):
        for file in files_to_be_deleted:
            delete(file)

    with Lock() as lock:
        lock.start_keep_alive()

        files_to_be_uploaded = get_files_to_be_uploaded()
        files_to_be_deleted = get_files_to_be_deleted()

        upload_files(files_to_be_uploaded)
        delete_files(files_to_be_deleted)
