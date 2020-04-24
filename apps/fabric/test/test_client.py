import asyncio
import toml

from apps.fabric.Client import Client

async def main(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']

    servers = config["servers"]
    for server in servers:
        print(server)
    
    client = Client(n, t, servers)
    mask = await client.get_inputmask(0)
    print(mask)


if __name__ == "__main__":
    config_file = "apps/fabric/test/config.toml"
    asyncio.run(main(config_file))