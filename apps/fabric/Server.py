import asyncio
import logging
import time

from aiohttp import web
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF
from honeybadgermpc.offline_randousha import randousha
from honeybadgermpc.utils.misc import wrap_send, subscribe_recv

field = GF(Subgroup.BLS12_381)

class Server:
    def __init__(self, n, t, node_id, send, recv, host, node_port, client_req_port):
        self.n = n
        self.t = t
        self.node_id = node_id

        # self._subscribe_task, subscribe = subscribe_recv(recv)
        # def get_send_recv(tag):
        #     return wrap_send(tag, send), subscribe(tag)
        # self.get_send_recv = get_send_recv
        from honeybadgermpc.utils.misc import _get_pubsub_channel

        self.subscribe_task, self.channel = _get_pubsub_channel(send, recv)
        self.get_send_recv = self.channel
        
        self.host = host
        self.node_port = node_port
        self.client_req_port = client_req_port
        
        self.inputmasks = []
        self.used_inputmasks = 0

    async def gen_inputmasks(self):
        k = 1
        target = 10
        preproc_round = 0
        while True:
            while True:
                if len(self.inputmasks) - self.used_inputmasks <= target:
                    break
                await asyncio.sleep(50)

            # Run Randousha
            logging.info(
                f"[{self.node_id}] len(inputmasks): {len(self.inputmasks)} \
                used_inputmasks: {self.used_inputmasks} \
                target: {target} Initiating Randousha {k * (self.n - 2 * self.t)}"
            )
            send, recv = self.get_send_recv(f"preproc:inputmasks {preproc_round}")
            # start_time = time.time()
            rs_t, rs_2t = zip(*await randousha(self.n, self.t, k, self.node_id, send, recv, field))
            assert len(rs_t) == len(rs_2t) == k * (self.n - 2 * self.t)

            # Note: here we just discard the rs_2t
            # In principle both sides of randousha could be used with
            # a small modification to randousha
            end_time = time.time()
            # logging.info(f"[{self.myid}] Randousha finished in {end_time-start_time}")
            # logging.info(f"len(rs_t): {len(rs_t)}")
            # logging.info(f"rs_t: {rs_t}")
            self.inputmasks += rs_t
            # logging.info(f"inputmasks: {inputmasks}")


            preproc_round += 1

    async def client_req_inputmask(self):
        routes = web.RouteTableDef()

        @routes.get("/inputmasks/{mask_idx}")
        async def _handler(request):
            mask_idx = int(request.match_info.get("mask_idx"))
            data = {
                "inputmask": self.inputmasks[mask_idx],
                "server_id": self.node_id,
                "server_port": self.client_req_port,
            }
            return web.json_response(data)

        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.client_req_port)
        await site.start()
        logging.info(f"======= Serving on http://{self.host}:{self.client_req_port}/ ======")
        # pause here for very long time by serving HTTP requests and
        # waiting for keyboard interruption
        await asyncio.sleep(100 * 3600)