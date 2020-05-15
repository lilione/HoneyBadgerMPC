import asyncio
import sys
import toml

from apps.fabric.src.client.Client import Client
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

def get_local_host():
    file = open('/etc/hosts', 'r')
    lines = file.readlines()
    line = lines[6]
    return line.split('\t')[0]

if __name__ == '__main__':
    inputmask_idx = sys.argv[1]
    masked_input = int(sys.argv[2])

    client = create_client('apps/fabric/conf/config.toml')

    host = get_local_host()
    print(host)

    inputmask_share = asyncio.run(client.req_local_mask_share(host, inputmask_idx))

    share = field(masked_input - inputmask_share)
    
    print("share", share)
