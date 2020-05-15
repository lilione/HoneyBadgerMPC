import asyncio
import sys
import toml

from apps.fabric.src.client.Client import Client

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
    share = sys.argv[1]

    client = create_client("apps/fabric/conf/config.toml")

    host = get_local_host()

    result = asyncio.run(client.req_start_reconstrct(host, share))
    print("result", result)