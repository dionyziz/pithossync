import unittest
import logging

import test.all_tests


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('pithossync')

logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s'))
logger.addHandler(handler)

testSuite = test.all_tests.create_test_suite()
textRunner = unittest.TextTestRunner().run(testSuite)
