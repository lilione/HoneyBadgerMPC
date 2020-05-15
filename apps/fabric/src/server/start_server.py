import asyncio
import sys
import toml

from honeybadgermpc.config import NodeDetails
from honeybadgermpc.ipc import NodeCommunicator
from apps.fabric.src.server.Server import Server

async def main(node_id, config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']

    # For NodeCommunicator
    node_details = {
        i: NodeDetails(s["host"], s["nc_port"])
        for i, s in enumerate(config["servers"])
    }

    # NodeCommunicator / zeromq sockets
    nc = NodeCommunicator(node_details, node_id, 2)
    await nc._setup()

    server_config = config["servers"][node_id]
    server = Server(n, t, node_id, nc.send, nc.recv, server_config["host"], server_config["nc_port"], server_config["http_port"])

    tasks = []
    tasks.append(asyncio.ensure_future(server.gen_inputmasks()))
    tasks.append(asyncio.ensure_future(server.client_req_inputmask()))

    for task in tasks:
        await task

if __name__ == "__main__":
    node_id = int(sys.argv[1])
    config_file = "apps/fabric/conf/config.toml"
    asyncio.run(main(node_id, config_file))