from __future__ import absolute_import
from pithossync.workingcopy import WorkingCopy


class Syncer:
    def __init__(self, url, token, account, container):
        self.url = url
        self.token = token
        self.account = account
        self.container = container
        self.client = PithosClient(self.url, self.token,
                                   self.account, self.container)

    def clone(self, local, remote):
        try:
            if not os.listdir(local) == []:
                raise DirectoryNotEmptyError()
        except OSError:
            try:
                print('Making local directory "%s"' % local)
                os.mkdir(local)
            except OSError:
                raise
        # except TypeError: # if local is not a string
        working_copy = WorkingCopy(self, local, remote)
        try:
            working_copy.clone()
            return working_copy
        except FileNotFoundError as e:
            try:
                working_copy.destroy()
                os.rmdir(local)
            except OSError:
                pass
            raise e

    def working_copy(self, local):
        working_copy = WorkingCopy(self, local)
        return working_copy
