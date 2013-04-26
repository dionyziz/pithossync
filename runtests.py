import unittest
import logging
import sys

import test.all_tests


logging.basicConfig(level=logging.DEBUG)

loggers_disabled = [
    'clients.recv',
    'clients.send',
    'data.recv',
    'data.send',
    'kamaki',
    'objpool'
]

for logger_name in loggers_disabled:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)

logger = logging.getLogger('pithossync')
logger.setLevel(logging.DEBUG)
logger.propagate = False

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s'))
logger.addHandler(handler)

if len(sys.argv) > 1:
    which = sys.argv[1]
else:
    which = '*'

testSuite = test.all_tests.create_test_suite(which=which)
textRunner = unittest.TextTestRunner().run(testSuite)
