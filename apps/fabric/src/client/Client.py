import asyncio
import logging

from aiohttp import ClientSession
from honeybadgermpc.polynomial import EvalPoint, polynomials_over
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

class Client:
    def __init__(self, n, t, servers):
        self.n = n
        self.t = t
        self.servers = servers

    # **** call from local fabric peer ****
    async def req_local_mask_share(self, host, mask_idx):
        port = -1
        import socket
        for server in self.servers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, server['http_port'])) == 0:
                    port = server['http_port']

        logging.info(
            f"query server {host}:{port} "
            f"for inputmask with id {mask_idx}"
        )
        url = f"http://{host}:{port}/inputmasks/{mask_idx}"
        async with ClientSession() as session:
            async with session.get(url) as resp:
                json_response = await resp.json()
        return json_response["inputmask_share"]

    async def req_start_reconstrct(self, host, share):
        port = -1
        import socket
        for server in self.servers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, server['http_port'])) == 0:
                    port = server['http_port']

        logging.info(
            f"query server {host}:{port} "
            f"start reconstruction with share {share}"
        )

        url = f"http://{host}:{port}/start_reconstruction/{share}"
        result = await self.send_request(host, port, url)
        return result["value"]

    async def req_cmp(self, host, share_a, share_b):
        port = -1
        import socket
        for server in self.servers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, server['http_port'])) == 0:
                    port = server['http_port']

        logging.info(
            f"query server {host}:{port} "
            f"cmp between share_a {share_a} share_b {share_b}"
        )

        url = f"http://{host}:{port}/cmp/{share_a}+{share_b}"
        result = await self.send_request(host, port, url)
        return result["result"]

    async def req_eq(self, host, share_a, share_b):
        port = -1
        import socket
        for server in self.servers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, server['http_port'])) == 0:
                    port = server['http_port']

        logging.info(
            f"query server {host}:{port} "
            f"cmp between share_a {share_a} share_b {share_b}"
        )

        url = f"http://{host}:{port}/eq/{share_a}+{share_b}"
        result = await self.send_request(host, port, url)
        return result["result"]

    # async def test_cmp(self, share_a, share_b):
    #     tasks = []
    #     for server in self.servers:
    #         host = server["host"]
    #         port = server["http_port"]
    #
    #         server_id = server["id"]
    #         print(server_id)
    #         url = f"http://{host}:{port}/cmp/{share_a[server_id]}+{share_b[server_id]}"
    #
    #         task = asyncio.ensure_future(self.send_request(host, port, url))
    #         tasks.append(task)
    #
    #     for task in tasks:
    #         await task
    #
    #     for task in tasks:
    #         print(task.result())

    # async def test_cmp(self, shares, idx_a, masked_a, idx_b, masked_b):
    #     tasks = []
    #     for server in self.servers:
    #         host = server["host"]
    #         port = server["http_port"]
    #
    #         server_id = server["id"]
    #         print(server_id)
    #         share_a = masked_a - shares[idx_a][server_id][1]
    #         share_b = masked_b - shares[idx_b][server_id][1]
    #         url = f"http://{host}:{port}/cmp/{share_a}+{share_b}"
    #
    #         task = asyncio.ensure_future(self.send_request(host, port, url))
    #         tasks.append(task)
    #
    #     for task in tasks:
    #         await task
    #
    #     for task in tasks:
    #         print(task.result())
    #
    # async def test_eq(self, shares, idx_a, masked_a, idx_b, masked_b):
    #     tasks = []
    #     for server in self.servers:
    #         host = server["host"]
    #         port = server["http_port"]
    #
    #         server_id = server["id"]
    #         print(server_id)
    #         share_a = masked_a - shares[idx_a][server_id][1]
    #         share_b = masked_b - shares[idx_b][server_id][1]
    #         url = f"http://{host}:{port}/eq/{share_a}+{share_b}"
    #
    #         task = asyncio.ensure_future(self.send_request(host, port, url))
    #         tasks.append(task)
    #
    #     for task in tasks:
    #         await task
    #
    #     for task in tasks:
    #         print(task.result())

    # **** call from remote client ****
    async def send_request(self, host, port, url):
        logging.info(
            f"query server {host}:{port} "
            f"send request {url} to mpc server"
        )
        async with ClientSession() as session:
            async with session.get(url) as resp:
                json_response = await resp.json()
                return json_response

    async def get_inputmask(self, mask_idx):
        tasks = []
        for server in self.servers:
            host = server["host"]
            port = server["http_port"]

            server_id = server["id"]
            print(server_id)

            url = f"http://{host}:{port}/inputmasks/{mask_idx}"

            task = asyncio.ensure_future(self.send_request(host, port, url))
            tasks.append(task)

        for task in tasks:
            await task

        shares = []
        for task in tasks:
            shares.append(task.result()["inputmask_share"])

        logging.info(
            f"{len(shares)} of input mask shares have"
            "been received from the MPC servers"
        )
        logging.info(
            "privately reconstruct the input mask from the received shares ..."
        )
        poly = polynomials_over(field)
        eval_point = EvalPoint(field, self.n, use_omega_powers=False)
        shares = [(eval_point(i), share) for i, share in enumerate(shares)]
        mask = poly.interpolate_at(shares, 0)
        return mask, shares
    
    # async def start_reconstruction(self, input, shares):
    #     tasks = []
    #     for server in self.servers:
    #         host = server["host"]
    #         port = server["http_port"]
    #
    #         server_id = server["id"]
    #         print(server_id)
    #         inputmask_share = shares[server_id][1]
    #         share = input - inputmask_share
    #         print(server["http_port"], share)
    #         url = f"http://{host}:{port}/start_reconstruction/{share}"
    #
    #         task = asyncio.ensure_future(self.send_request(host, port, url))
    #         tasks.append(task)
    #
    #     for task in tasks:
    #         await task
    #
    #     for task in tasks:
    #         print(task.result()['value'])