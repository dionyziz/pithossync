import glob
import unittest
import pithossync

def create_test_suite(which='*'):
    test_file_strings = glob.glob('test/test_%s.py' % which)
    module_strings = ['test.' + str[len('test/'):len(str) - len('.py')]
                      for str in test_file_strings]
    suites = [unittest.defaultTestLoader.loadTestsFromName(name)
              for name in module_strings]
    testSuite = unittest.TestSuite(suites)
    return testSuite
