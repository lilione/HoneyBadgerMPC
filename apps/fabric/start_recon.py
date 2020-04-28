import asyncio
import logging
import toml

from aiohttp import ClientSession

async def start_reconstruction(self):
    for server in self.servers:
        print(server)
        host = server["host"]
        port = server["http_port"]
        logging.info(
            f"query server {host}:{port}"
            f"start reconstruction"
        )
        url = f"http://{host}:{port}/start_reconstruction"
        async with ClientSession() as session:
            async with session.get(url) as resp:
                json_response = await resp.json()
        print("response", json_response)

async def main(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']

    servers = config["servers"]
    for server in servers:
        print(server)

    await start_reconstruction()


if __name__ == "__main__":
    config_file = "apps/fabric/conf/config.toml"
    asyncio.run(main(config_file))