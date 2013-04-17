def clone(working_copy):
    print("Using account '%s' on Pithos server '%s'." %
          (working_copy.syncer.account, working_copy.syncer.url))
    print("Cloning folder '%s' from remote container '%s' "
          "into local directory '%s'..." %
          (working_copy.folder, working_copy.syncer.container, working_copy.local))
    LocalMetaFile().create(remote_server, remote_container, remote_dir, local_dir)
    working_copy.pull()
