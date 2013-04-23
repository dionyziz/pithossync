def init(working_copy):
    working_copy.lock.init()
    working_copy.meta_file.create(working_copy.local, working_copy.remote_container)

    for folder in working_copy.folder.split('/'):
        print(folder)

    working_copy.clone()
