#!/home/dionyziz/env/bin/python
import sys
import os
from ConfigParser import ConfigParser
from optparse import OptionParser

import pithossync


defaults = {
    'url': '',
    'account': '',
    'token': '',
    'container': ''
}

config = ConfigParser()
try:
    config.read(os.path.expanduser('~/.pithosconfig'))
    for key in defaults.keys():
        try:
            defaults[key] = config.get('pithos', key)
        except:
            pass
except:
    pass

parser = OptionParser()
parser.add_option('-u', '--url', dest='url', default=defaults['url'],
                  help='Specify the URL of the running pithos service')
parser.add_option('-a', '--account', dest='account', default=defaults['account'],
                  help='Sets the e-mail address of the account with which you want to access pithos')
parser.add_option('-t', '--token', dest='token', default=defaults['token'],
                  help='Provides the astakos authentication token to use with pithos')
parser.add_option('-c', '--container', dest='container', default=defaults['container'],
                  help='Sets the desired pithos container')
# TODO: Switch to argparse
(options, args) = parser.parse_args()

def syntax():
    # TODO: Syntax should be automatically generated
    print('Syntax: pithos [OPTIONS] clone remote local')
    print('        pithos [OPTIONS] pull local')
    print('        pithos [OPTIONS] push local')

if len(args) < 1:
    syntax()
    sys.exit(0)
else:
    command = args[0]
    syncer = pithossync.Syncer(options.url, options.token, options.account, options.container)
    try:
        if command == 'clone':
            try:
                remote = args[1]
            except:
                syntax()
                sys.exit(0)
            try:
                local = args[2]
            except:
                local = os.path.split(remote)[1]
            syncer.clone(local, remote)
        if command == 'push':
            try:
                local = args[1]
            except:
                local = '.'
            working_copy = syncer.working_copy(local)
            working_copy.push()
        if command == 'pull':
            try:
                local = args[1]
            except:
                local = '.'
            working_copy = syncer.working_copy(local)
            working_copy.pull()
    except pithossync.DirectoryNotEmptyError:
        print('Directory "%s" is not empty.' % local)
    except pithossync.FileNotFoundError:
        print('Directory "%s" does not exist.' % local)
    except pithossync.InvalidWorkingCopyError:
        print('Directory "%s" is not a working copy.' % local)
    except OSError:
        print('Directory "%s" could not be created. Check permissions?')
