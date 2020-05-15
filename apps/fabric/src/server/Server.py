import asyncio
import logging
import time

from aiohttp import web
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF
from honeybadgermpc.mpc import Mpc
from honeybadgermpc.offline_randousha import randousha

field = GF(Subgroup.BLS12_381)

class Server:
    def __init__(self, n, t, node_id, send, recv, host, node_port, http_port):
        self.n = n
        self.t = t
        self.node_id = node_id

        from honeybadgermpc.utils.misc import _get_pubsub_channel

        self.subscribe_task, self.channel = _get_pubsub_channel(send, recv)
        self.get_send_recv = self.channel
        
        self.host = host
        self.node_port = node_port
        self.http_port = http_port
        
        self.inputmasks = []
        self.max_inputmask_idx = 0

        self.epoch = 0

    async def gen_inputmasks(self):
        k = 1
        target = 10
        preproc_round = 0
        while True:
            while True:
                if len(self.inputmasks) - self.max_inputmask_idx <= target:
                    break
                await asyncio.sleep(50)

            # Run Randousha
            logging.info(
                f"[{self.node_id}] len(inputmasks): {len(self.inputmasks)} \
                used_inputmasks: {self.max_inputmask_idx} \
                target: {target} Initiating Randousha {k * (self.n - 2 * self.t)}"
            )
            send, recv = self.get_send_recv(f"preproc:inputmasks {preproc_round}")
            rs_t, rs_2t = zip(*await randousha(self.n, self.t, k, self.node_id, send, recv, field))
            assert len(rs_t) == len(rs_2t) == k * (self.n - 2 * self.t)

            print(rs_t)
            self.inputmasks += rs_t

            preproc_round += 1

    async def reconstruction(self, share):
        async def prog(ctx):
            logging.info(f"[{ctx.myid}] Running MPC network")
            msg_share = ctx.Share(share)
            opened_value = await msg_share.open()
            return opened_value
            # opened_value_bytes = opened_value.value.to_bytes(32, "big")
            # logging.info(f"opened_value in bytes: {opened_value_bytes}")
            # msg = opened_value_bytes.decode().strip("\x00")
            # return msg

        self.epoch += 1
        send, recv = self.get_send_recv(f"mpc:{self.epoch}")
        logging.info(f"[{self.node_id}] MPC initiated:{self.epoch}")
        config = {}
        ctx = Mpc(f"mpc:{self.epoch}", self.n, self.t, self.node_id, send, recv, prog, config)
        result = await ctx._run()
        logging.info(f"[{self.node_id}] MPC complete {result}")

        return result

    async def client_req_inputmask(self):
        routes = web.RouteTableDef()

        @routes.get("/inputmasks/{mask_idx}")
        async def _handler(request):
            print(request)
            mask_idx = int(request.match_info.get("mask_idx"))
            self.max_inputmask_idx = max(mask_idx, self.max_inputmask_idx)
            data = {
                "inputmask": self.inputmasks[mask_idx],
                "server_id": self.node_id,
                "server_port": self.http_port,
            }
            return web.json_response(data)
        
        @routes.get(("/start_reconstruction/{share}"))
        async def _handler(request):
            print("request", request)
            share = int(request.match_info.get("share")[1:-1])
            print("share", share)
            
            res = await self.reconstruction(share)
            print(res)

            data = {
                "value": int(res),
            }
            return web.json_response(data)

        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.http_port)
        await site.start()
        logging.info(f"======= Serving on http://{self.host}:{self.http_port}/ ======")
        # pause here for very long time by serving HTTP requests and
        # waiting for keyboard interruption
        await asyncio.sleep(100 * 3600)
        