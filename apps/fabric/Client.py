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

    async def req_mask_shares(self, mask_idx):
        shares = []
        for server in self.servers:
            print(server)
            host = server["host"]
            port = server["client_req_port"]
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
        return mask