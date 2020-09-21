import asyncio
import sys

from apps.fabric.src.client.Client import Client

if __name__ == '__main__':
    share = sys.argv[1]

    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    local_host = client.get_local_host()
    local_port = client.get_port(local_host)

    value = asyncio.run(client.req_recon(local_host, local_port, share))
    print("value", value)