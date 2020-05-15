import asyncio
import toml
from honeybadgermpc.router import SimpleRouter
from apps.fabric.src.server.Server import Server

async def main(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']

    # communication channels
    router = SimpleRouter(n)
    sends, recvs = router.sends, router.recvs

    servers = []
    for i in range(n):
        server_config = config["servers"][i]
        server = Server(n, t, server_config["id"], sends[i], recvs[i], server_config["host"], server_config["port"])
        servers.append(server)

    tasks = []
    for server in servers:
        print(server)
        tasks.append(asyncio.ensure_future(server.gen_inputmasks()))
        tasks.append(asyncio.ensure_future(server.client_req_inputmask()))

    for task in tasks:
        await task

if __name__ == "__main__":
    config_file = "apps/fabric/conf/config.toml"
    asyncio.run(main(config_file))