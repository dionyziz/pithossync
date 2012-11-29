import pithossync
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-u', '--url', dest='url', default='https://pithos.okeanos.grnet.gr/v1',
                  help='Specify the URL of the running pithos service')
parser.add_option('-a', '--account', dest='account', default='dionyziz@gmail.com',
                  help='Sets the e-mail address of the account with which you want to access pithos')
parser.add_option('-t', '--token', dest='token',
                  help='Provides the astakos authentication token to use with pithos')
parser.add_option('-c', '--container', dest='container', default='pithos',
                  help='Sets the desired pithos container')
(options, args) = parser.parse_args()

if len(args) != 3:
    print('Syntax: pithos [OPTIONS] command remote local')
else:
    command = args[0]
    remote = args[1]
    local = args[2]
    syncer = pithossync.Syncer(options.url, options.token, options.account, options.container)
    try:
        if command == 'clone':
            syncer.clone(local, remote)
        if command == 'push':
            working_copy = syncer.workingCopy(local, remote)
            working_copy.push()
        if command == 'pull':
            working_copy = syncer.workingCopy(local, remote)
            working_copy.pull()
    except pithossync.DirectoryNotEmptyError:
        print("The directory is not empty.")
    except pithossync.FileNotFoundError:
        print("The directory does not exist.")
