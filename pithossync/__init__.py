from lock import *
from syncer import *
from workingcopy import *
from push import *
from pull import *
from init import *
from clone import *

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

logger.debug('pithossync library loaded.')
