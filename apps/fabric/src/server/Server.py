import asyncio
import logging
import time

from aiohttp import web
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF
from honeybadgermpc.mpc import Mpc
from honeybadgermpc.offline_randousha import randousha
from honeybadgermpc.preprocessing import PreProcessedElements
from honeybadgermpc.progs.mixins.share_arithmetic import (
    BeaverMultiply,
    BeaverMultiplyArrays,
    DivideShareArrays,
    DivideShares,
    InvertShare,
    InvertShareArray,
)
from honeybadgermpc.progs.mixins.share_comparison import Equality, LessThan

STANDARD_ARITHMETIC_MIXINS = [
    BeaverMultiply(),
    BeaverMultiplyArrays(),
    InvertShare(),
    InvertShareArray(),
    DivideShares(),
    DivideShareArrays(),
    Equality(),
    LessThan(),
]

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

        # pp_elements = PreProcessedElements()
        # pp_elements.generate_share_bits(1, self.n, self.t)
        # pp_elements.generate_triples(200, self.n, self.t)
        # pp_elements.generate_bits(200, self.n, self.t)
        # pp_elements.generate_rands(100, self.n, self.t)

    async def gen_inputmasks(self):
        k = 1
        target = 10
        preproc_round = 0
        while True:
            while True:
                if len(self.inputmasks) - self.max_inputmask_idx <= target:
                    break
                await asyncio.sleep(10)

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

        self.epoch += 1
        send, recv = self.get_send_recv(f"mpc:{self.epoch}")
        logging.info(f"[{self.node_id}] MPC initiated:{self.epoch}")
        config = {}
        ctx = Mpc(f"mpc:{self.epoch}", self.n, self.t, self.node_id, send, recv, prog, config)
        result = await ctx._run()
        logging.info(f"[{self.node_id}] MPC complete {result}")

        return result

    async def cmp(self, share_a, share_b):
        async def prog(ctx):
            return await (ctx.Share(share_a) < ctx.Share(share_b)).open()

        self.epoch += 1
        send, recv = self.get_send_recv(f"mpc:{self.epoch}")
        logging.info(f"[{self.node_id}] MPC initiated:{self.epoch}")
        config = {}
        for mixin in STANDARD_ARITHMETIC_MIXINS:
            config[mixin.name] = mixin
        ctx = Mpc(f"mpc:{self.epoch}", self.n, self.t, self.node_id, send, recv, prog, config)
        result = await ctx._run()
        logging.info(f"[{self.node_id}] MPC complete {result}")

        return result

    async def eq(self, share_a, share_b):
        async def prog(ctx):
            return await (ctx.Share(share_a) == ctx.Share(share_b)).open()

        self.epoch += 1
        send, recv = self.get_send_recv(f"mpc:{self.epoch}")
        logging.info(f"[{self.node_id}] MPC initiated:{self.epoch}")
        config = {}
        for mixin in STANDARD_ARITHMETIC_MIXINS:
            config[mixin.name] = mixin
        ctx = Mpc(f"mpc:{self.epoch}", self.n, self.t, self.node_id, send, recv, prog, config)
        result = await ctx._run()
        logging.info(f"[{self.node_id}] MPC complete {result}")

        return result

    async def enough_mask(self, mask_idx):
        while True:
            if mask_idx < len(self.inputmasks):
                break
            await asyncio.sleep(2)

    async def http_server(self):
        routes = web.RouteTableDef()

        @routes.get("/inputmasks/{mask_idx}")
        async def _handler(request):
            print(request)
            mask_idx = int(request.match_info.get("mask_idx"))
            self.max_inputmask_idx = max(mask_idx, self.max_inputmask_idx)
            await self.enough_mask(mask_idx)
            data = {
                "inputmask_share": self.inputmasks[mask_idx],
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

        @routes.get(("/cmp/{share_a}+{share_b}"))
        async def _handler(request):
            print("request", request)
            share_a = int(request.match_info.get("share_a")[1:-1])
            share_b = int(request.match_info.get("share_b")[1:-1])
            print("share_a", share_a)
            print("share_b", share_b)

            res = await self.cmp(share_a, share_b)
            print(res)

            data = {
                "result": int(res),
            }
            return web.json_response(data)

        @routes.get(("/eq/{share_a}+{share_b}"))
        async def _handler(request):
            print("request", request)
            share_a = int(request.match_info.get("share_a")[1:-1])
            share_b = int(request.match_info.get("share_b")[1:-1])
            print("share_a", share_a)
            print("share_b", share_b)

            res = await self.eq(share_a, share_b)
            print(res)

            data = {
                "result": int(res),
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
        