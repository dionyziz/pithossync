from kamaki.clients.pithos import PithosClient, ClientError
import logging
import os


logging.basicConfig(level=logging.DEBUG)

url = 'https://pithos.okeanos.io/v1'
account = 'd8e6f8bb-619b-4ce6-8903-89fabdca024d'
container = 'pithos'
token = os.getenv('ASTAKOS_TOKEN', '')

client = PithosClient(url, token,
                      account, container)

client.create_directory('break-pithos')

for i in range(0, 100):
    client.object_delete('break-pithos')
    client.create_directory('break-pithos')
