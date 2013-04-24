from __future__ import absolute_import
import os
import logging

from kamaki.clients.pithos import PithosClient, ClientError
from kamaki.clients import logger

from pithossync.workingcopy import WorkingCopy, InvalidWorkingCopyError


logger = logging.getLogger(__name__)


class DirectoryNotEmptyError(Exception):
    pass


class ConflictError(Exception):
    pass


class Syncer:
    """Main entry point for the usage of the pithos sync library. Other modules should not be used
       directly."""

    # TODO: Move 'container' and 'url' into working copy? Disallow from syncer constructor?
    #       Change class API hierarchy to allow top-level working copies?
    def __init__(self, url, token, account, container):
        self.url = url
        self.token = token
        self.account = account
        self.container = container
        self.client = PithosClient(self.url, self.token,
                                   self.account, self.container)

    def init(self, local, remote):
        self.prepare_for_init_or_clone(local, remote)

        working_copy = WorkingCopy(self, local, remote)
        working_copy.init()

    def prepare_for_init_or_clone(self, local, remote):
        """Creates the appropriate directories before a clone/init operation."""

        try:
            if not os.listdir(local) == []:
                raise DirectoryNotEmptyError
        except OSError:
            try:
                logger.info('Making local directory "%s"' % local)
                os.mkdir(local)
            except OSError:
                raise

    def clone(self, local, remote):
        """Creates the appropriate directories, ensures the target folder is empty, and initiates a clone operaiton."""

        self.prepare_for_init_or_clone(local, remote)

        # except TypeError: # if local is not a string
        working_copy = WorkingCopy(self, local, remote)
        try:
            working_copy.clone()
            return working_copy
        except InvalidWorkingCopyError as e:
            try:
                working_copy.destroy()
                os.rmdir(local)
            except OSError:
                pass
            raise e

    def working_copy(self, local):
        working_copy = WorkingCopy(self, local)
        return working_copy
