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
        
    async def req_local_mask_share(self, host, mask_idx):
        port = -1
        import socket
        for server in self.servers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, server['http_port'])) == 0:
                    port = server['http_port']

        logging.info(
            f"query server {host}:{port} "
            f"for its share of input mask with id {mask_idx}"
        )
        url = f"http://{host}:{port}/inputmasks/{mask_idx}"
        async with ClientSession() as session:
            async with session.get(url) as resp:
                json_response = await resp.json()
        share = json_response["inputmask"]
        return share
    
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
        return result

    async def req_mask_shares(self, mask_idx):
        shares = []
        for server in self.servers:
            host = server["host"]
            port = server["http_port"]
            logging.info(
                f"query server {host}:{port} "
                f"for its share of input mask with id {mask_idx}"
            )
            url = f"http://{host}:{port}/inputmasks/{mask_idx}"
            async with ClientSession() as session:
                async with session.get(url) as resp:
                    json_response = await resp.json()
            share = json_response["inputmask"]
            shares.append(share)
        return shares

    async def get_inputmask(self, mask_idx):
        # Private reconstruct
        poly = polynomials_over(field)
        eval_point = EvalPoint(field, self.n, use_omega_powers=False)
        shares = await self.req_mask_shares(mask_idx)
        logging.info(
            f"{len(shares)} of input mask shares have"
            "been received from the MPC servers"
        )
        logging.info(
            "privately reconstruct the input mask from the received shares ..."
        )
        shares = [(eval_point(i), share) for i, share in enumerate(shares)]
        mask = poly.interpolate_at(shares, 0)
        return mask, shares

    async def send_request(self, host, port, url):
        logging.info(
            f"query server {host}:{port} "
            f"send input {input} to mpc server"
        )
        async with ClientSession() as session:
            async with session.get(url) as resp:
                json_response = await resp.json()
                return json_response['value']
    
    async def start_reconstruction(self, input, shares):
        tasks = []
        for server in self.servers:
            host = server["host"]
            port = server["http_port"]

            server_id = server["id"]
            print(server_id)
            inputmask_share = shares[server_id][1]
            share = input - inputmask_share
            print(server["http_port"], share)
            url = f"http://{host}:{port}/start_reconstruction/{share}"

            task = asyncio.ensure_future(self.send_request(host, port, url))
            tasks.append(task)

        for task in tasks:
            await task

        for task in tasks:
            print(task.result())

