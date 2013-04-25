from kamaki.clients.pithos import PithosClient, ClientError
import logging
import threading
import os


container = 'pithos'

# url = 'https://pithos.okeanos.io/v1'
# account = 'd8e6f8bb-619b-4ce6-8903-89fabdca024d'

url = 'https://pithos.okeanos.grnet.gr/v1'
account = '60dd7c4c-71ff-4156-b387-aaeea33763cb'
token = os.getenv('ASTAKOS_TOKEN', '')

client = PithosClient(url, token,
                      account, container)

client.create_directory('break-pithos')

N = 10
K = 2

def parallel(j):
    for i in range(0, N):
        print '#%i DELETE' % j
        try:
            client.object_delete('break-pithos')
        except:
            pass
        print '#%i PUT' % j
        client.create_directory('break-pithos')

for j in range(0, K):
    t = threading.Thread(target=parallel, args=(j,))
    t.start()
