import asyncio
import toml
from honeybadgermpc.router import SimpleRouter
from apps.fabric.Server import Server

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
        server = Server(server_config["id"], sends[i], recvs[i], server_config["host"], server_config["port"])
        servers.append(server)

    tasks = []
    for server in servers:
        print(server)
        task = asyncio.ensure_future(server.offline_inputmasks(n, t))
        tasks.append(task)

    for task in tasks:
        await task

if __name__ == "__main__":
    config_file = "apps/fabric/test/server.toml"
    asyncio.run(main(config_file))